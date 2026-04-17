# Interface gráfica para desktop do chat automático em rede local (LAN).

# A interface padrão é uma janela nativa que renderiza a mesma interface web usada
# pelo modo navegador, preservando o HTML, CSS e JavaScript originais.

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import random
import socket
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from typing import Any
from urllib.parse import urlparse

from discovery import DISCOVERY_PORT, DiscoveryResponder, discover_server
from protocol import ProtocolError, recv_packet, send_packet
from server import DEFAULT_PORT, ChatServer


FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8080


class GuiChatSession:
    # Gerencia uma conexão de chat TCP para a interface de usuário local.

    def __init__(
        self,
        chat_port: int,
        discovery_port: int,
        discovery_timeout: float,
        server_name: str,
    ) -> None:
        self.chat_port = chat_port
        self.discovery_port = discovery_port
        self.discovery_timeout = discovery_timeout
        self.server_name = server_name
        self.subscribers: list[Queue[dict[str, Any]]] = []
        self.backlog: list[dict[str, Any]] = []
        self.event_lock = threading.Lock()
        self.lock = threading.Lock()
        self.connected = threading.Event()
        self.sock: socket.socket | None = None
        self.username: str | None = None
        self.hosting = False
        self.server: ChatServer | None = None
        self.server_thread: threading.Thread | None = None
        self.discovery_responder: DiscoveryResponder | None = None

    def start(self, username: str) -> dict[str, Any]:
        with self.lock:
            if self.connected.is_set():
                return {"connected": True, "username": self.username, "hosting": self.hosting}

            self.username = username.strip() or "user"
            offer = discover_server(self.discovery_port, self.discovery_timeout)
            if offer is None:
                time.sleep(random.uniform(0.2, 0.8))
                offer = discover_server(self.discovery_port, 0.8)

            if offer is None:
                self._start_local_server()
                host = "127.0.0.1"
                port = self.chat_port
                self.hosting = True
                self._publish_status("No active room found. Hosting a new room on this computer.")
            else:
                host = offer.host
                port = offer.port
                self.hosting = False
                self._publish_status(f"Connected to room {offer.name} at {host}:{port}.")

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
            send_packet(self.sock, {"type": "join", "username": self.username})
            self.connected.set()

            receiver = threading.Thread(target=self._receive_loop, daemon=True)
            receiver.start()

            return {
                "connected": True,
                "username": self.username,
                "host": host,
                "port": port,
                "hosting": self.hosting,
            }

    def send_message(self, text: str) -> None:
        if not text.strip():
            return
        self._send({"type": "message", "text": text})

    def send_file(self, filename: str, data: str) -> None:
        safe_name = Path(filename or "file").name
        self._send({"type": "file", "filename": safe_name, "data": data})

    def stop(self) -> None:
        with self.lock:
            self.connected.clear()
            if self.sock is not None:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.sock.close()
                self.sock = None

            if self.discovery_responder is not None:
                self.discovery_responder.stop()
                self.discovery_responder = None

            if self.server is not None:
                self.server.running.clear()
                self.server = None

            with self.event_lock:
                self.backlog.clear()

    def subscribe(self) -> Queue[dict[str, Any]]:
        queue: Queue[dict[str, Any]] = Queue()
        with self.event_lock:
            for packet in self.backlog:
                queue.put(packet)
            self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: Queue[dict[str, Any]]) -> None:
        with self.event_lock:
            if queue in self.subscribers:
                self.subscribers.remove(queue)

    def _start_local_server(self) -> None:
        self.server = ChatServer("0.0.0.0", self.chat_port)
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()

        self.discovery_responder = DiscoveryResponder(
            self.chat_port,
            self.discovery_port,
            self.server_name,
        )
        self.discovery_responder.start()

        if not self._wait_until_tcp_ready("127.0.0.1", self.chat_port, timeout=3.0):
            raise RuntimeError("local TCP server did not start")

    def _receive_loop(self) -> None:
        assert self.sock is not None
        try:
            while self.connected.is_set():
                packet = recv_packet(self.sock)
                self._publish(packet)
        except (ConnectionError, OSError, ProtocolError):
            if self.connected.is_set():
                self._publish_status("Connection closed.")
        finally:
            self.connected.clear()

    def _send(self, packet: dict[str, Any]) -> None:
        with self.lock:
            if self.sock is None or not self.connected.is_set():
                raise ConnectionError("chat session is not connected")
            send_packet(self.sock, packet)

    def _publish_status(self, message: str) -> None:
        self._publish({"type": "status", "message": message})

    def _publish(self, packet: dict[str, Any]) -> None:
        with self.event_lock:
            self.backlog.append(packet)
            self.backlog = self.backlog[-100:]
            subscribers = list(self.subscribers)

        for queue in subscribers:
            queue.put(packet)

    @staticmethod
    def _wait_until_tcp_ready(host: str, port: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.25):
                    return True
            except OSError:
                time.sleep(0.1)
        return False


class GuiRequestHandler(BaseHTTPRequestHandler):
    session: GuiChatSession

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/events":
            self._handle_events()
            return

        path = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self._read_json()
            if parsed.path == "/api/start":
                username = str(data.get("username", "user"))
                self._send_json(self.session.start(username))
                return
            if parsed.path == "/api/message":
                self.session.send_message(str(data.get("text", "")))
                self._send_json({"ok": True})
                return
            if parsed.path == "/api/file":
                filename = str(data.get("filename", "file"))
                file_data = str(data.get("data", ""))
                self._validate_base64(file_data)
                self.session.send_file(filename, file_data)
                self._send_json({"ok": True})
                return
            if parsed.path == "/api/stop":
                self.session.stop()
                self._send_json({"ok": True})
                return
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle_events(self) -> None:
        queue = self.session.subscribe()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            while True:
                try:
                    packet = queue.get(timeout=15)
                    payload = json.dumps(packet, ensure_ascii=False)
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                except Empty:
                    self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.session.unsubscribe(queue)

    def _serve_static(self, relative_path: str) -> None:
        file_path = (FRONTEND_DIR / relative_path).resolve()
        if FRONTEND_DIR not in file_path.parents and file_path != FRONTEND_DIR:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        data = json.loads(payload.decode("utf-8") or "{}")
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def _send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    @staticmethod
    def _validate_base64(data: str) -> None:
        base64.b64decode(data.encode("ascii"), validate=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Desktop HTML/CSS/JavaScript GUI for the automatic LAN chat")
    parser.add_argument("--ui-host", default=DEFAULT_UI_HOST, help="local UI host; default: 127.0.0.1")
    parser.add_argument("--ui-port", type=int, default=DEFAULT_UI_PORT, help="local UI port; default: 8080")
    parser.add_argument("--chat-port", type=int, default=DEFAULT_PORT, help="TCP chat port; default: 5050")
    parser.add_argument("--discovery-port", type=int, default=DISCOVERY_PORT, help="UDP discovery port; default: 5052")
    parser.add_argument("--timeout", type=float, default=2.0, help="discovery timeout in seconds; default: 2.0")
    parser.add_argument("--server-name", default="Chat TCP LAN", help="advertised room name when hosting")
    parser.add_argument("--web", action="store_true", help="open the same interface in the default browser")
    parser.add_argument("--no-browser", action="store_true", help="with --web, do not open the browser automatically")
    return parser.parse_args()


def run_web_interface(args: argparse.Namespace, session: GuiChatSession) -> None:
    class RequestHandler(GuiRequestHandler):
        pass

    RequestHandler.session = session
    server = ThreadingHTTPServer((args.ui_host, args.ui_port), RequestHandler)
    url = f"http://{args.ui_host}:{args.ui_port}"
    print(f"Chat GUI available at {url}")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GUI...")
    finally:
        session.stop()
        server.server_close()


def run_embedded_web_interface(args: argparse.Namespace, session: GuiChatSession) -> None:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("WebKit2", "4.1")
        from gi.repository import Gtk, WebKit2
    except (ImportError, ValueError) as exc:
        raise RuntimeError("GTK WebKit2 is not available") from exc

    class RequestHandler(GuiRequestHandler):
        pass

    RequestHandler.session = session
    server = ThreadingHTTPServer((args.ui_host, args.ui_port), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://{args.ui_host}:{args.ui_port}"
    window = Gtk.Window(title="Local Chat")
    window.set_default_size(980, 860)
    window.set_size_request(520, 420)

    web_view = WebKit2.WebView()
    web_view.load_uri(url)
    window.add(web_view)

    def close_window(_window: object) -> None:
        session.stop()
        server.shutdown()
        server.server_close()
        Gtk.main_quit()

    window.connect("destroy", close_window)
    window.show_all()
    Gtk.main()


def main() -> None:
    args = parse_args()
    session = GuiChatSession(args.chat_port, args.discovery_port, args.timeout, args.server_name)
    if args.web:
        run_web_interface(args, session)
    else:
        try:
            run_embedded_web_interface(args, session)
        except RuntimeError as exc:
            print(f"{exc}. Install GTK WebKit2 or run with --web to use the browser.")


if __name__ == "__main__":
    main()
