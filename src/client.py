"""Cliente de chat TCP para terminal implementado com sockets Berkeley."""

from __future__ import annotations

import argparse
import base64
import socket
import sys
import threading
from pathlib import Path

from protocol import ProtocolError, recv_packet, send_packet


DEFAULT_PORT = 5050
DOWNLOAD_DIR = Path("downloads")


class ChatClient:
    """Cliente que envia dados do usuário e recebe transmissões do servidor simultaneamente."""

    def __init__(self, host: str, port: int, username: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = threading.Event()
        self.connected.set()

    def start(self) -> None:
        self.sock.connect((self.host, self.port))
        send_packet(self.sock, {"type": "join", "username": self.username})

        receiver = threading.Thread(target=self._receive_loop, daemon=True)
        receiver.start()

        print("Commands: /file PATH sends a file, /quit leaves the chat.")
        try:
            while self.connected.is_set():
                line = input()
                if line.strip() == "/quit":
                    break
                if line.startswith("/file "):
                    self._send_file(Path(line[6:].strip()))
                elif line.strip():
                    send_packet(self.sock, {"type": "message", "text": line})
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self.connected.clear()
            self._close()

    def _receive_loop(self) -> None:
        try:
            while self.connected.is_set():
                packet = recv_packet(self.sock)
                self._render_packet(packet)
        except (ConnectionError, OSError, ProtocolError):
            if self.connected.is_set():
                print("\nConnection closed by server.")
        finally:
            self.connected.clear()

    def _render_packet(self, packet: dict[str, object]) -> None:
        packet_type = packet.get("type")
        timestamp = packet.get("timestamp", "")

        if packet_type == "message":
            sender = packet.get("from", "unknown")
            text = packet.get("text", "")
            print(f"[{timestamp}] {sender}: {text}")
        elif packet_type == "system":
            print(f"[{timestamp}] * {packet.get('message', '')}")
        elif packet_type == "file":
            self._save_file(packet)
        elif packet_type == "error":
            print(f"[{timestamp}] ! {packet.get('message', '')}")

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            print(f"File not found: {path}")
            return

        data = base64.b64encode(path.read_bytes()).decode("ascii")
        send_packet(
            self.sock,
            {
                "type": "file",
                "filename": path.name,
                "data": data,
            },
        )

    def _save_file(self, packet: dict[str, object]) -> None:
        sender = str(packet.get("from", "unknown"))
        filename = Path(str(packet.get("filename", "file"))).name
        data = packet.get("data")
        timestamp = packet.get("timestamp", "")

        if not isinstance(data, str):
            print(f"[{timestamp}] ! Invalid file received from {sender}")
            return

        DOWNLOAD_DIR.mkdir(exist_ok=True)
        target = self._next_available_path(DOWNLOAD_DIR / f"{sender}_{filename}")
        try:
            target.write_bytes(base64.b64decode(data.encode("ascii"), validate=True))
        except ValueError:
            print(f"[{timestamp}] ! Invalid file data received from {sender}")
            return

        print(f"[{timestamp}] * File received from {sender}: {target}")

    @staticmethod
    def _next_available_path(path: Path) -> Path:
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 2
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _close(self) -> None:
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAN TCP chat client")
    parser.add_argument("host", help="server IP address on the local network")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="TCP port; default: 5050")
    parser.add_argument("--username", "-u", required=True, help="name shown in the chat")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        ChatClient(args.host, args.port, args.username).start()
    except ConnectionRefusedError:
        print("Connection refused. Check that the server is running and the port is open.")
        sys.exit(1)
    except OSError as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
