#Servidor de bate-papo TCP multi-cliente implementado com sockets Berkeley.

from __future__ import annotations

import argparse
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from protocol import ProtocolError, recv_packet, send_packet


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5050


@dataclass
class Client:
    sock: socket.socket
    address: tuple[str, int]
    username: str


class ChatServer:
    # Servidor central responsável pelo gerenciamento de conexões e transmissão de dados.

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.clients: dict[socket.socket, Client] = {}
        self.clients_lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()

    def start(self) -> None:
        # Começa a aceitar clientes TCP até que seja interrompido

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen()
            server_sock.settimeout(1.0)

            print(f"Server listening on {self.host}:{self.port}")
            print("Press Ctrl+C to stop.")

            try:
                while self.running.is_set():
                    try:
                        client_sock, address = server_sock.accept()
                    except socket.timeout:
                        continue

                    client_sock.settimeout(120.0)
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_sock, address),
                        daemon=True,
                    )
                    thread.start()
            except KeyboardInterrupt:
                print("\nStopping server...")
            finally:
                self.running.clear()
                self._close_all_clients()

    def _handle_client(self, client_sock: socket.socket, address: tuple[str, int]) -> None:
        client: Client | None = None

        try:
            join_packet = recv_packet(client_sock)
            if join_packet.get("type") != "join":
                send_packet(client_sock, {"type": "error", "message": "first packet must be join"})
                return

            username = self._unique_username(str(join_packet.get("username", "")).strip())
            client = Client(sock=client_sock, address=address, username=username)

            with self.clients_lock:
                self.clients[client_sock] = client

            send_packet(
                client_sock,
                {
                    "type": "system",
                    "timestamp": self._timestamp(),
                    "message": f"Connected as {username}.",
                },
            )
            self._broadcast_system(f"{username} joined the chat.")
            print(f"{username} connected from {address[0]}:{address[1]}")

            while self.running.is_set():
                packet = recv_packet(client_sock)
                self._dispatch_packet(client, packet)
        except (ConnectionError, OSError, ProtocolError):
            pass
        finally:
            if client is not None:
                self._remove_client(client)
            else:
                self._safe_close(client_sock)

    def _dispatch_packet(self, client: Client, packet: dict[str, Any]) -> None:
        packet_type = packet.get("type")

        if packet_type == "message":
            text = str(packet.get("text", "")).strip()
            if text:
                self._broadcast(
                    {
                        "type": "message",
                        "timestamp": self._timestamp(),
                        "from": client.username,
                        "text": text,
                    }
                )
            return

        if packet_type == "file":
            self._handle_file_packet(client, packet)
            return

        if packet_type == "ping":
            self._send_to(client.sock, {"type": "pong", "timestamp": self._timestamp()})
            return

        self._send_to(
            client.sock,
            {
                "type": "error",
                "timestamp": self._timestamp(),
                "message": f"unknown packet type: {packet_type}",
            },
        )

    def _handle_file_packet(self, client: Client, packet: dict[str, Any]) -> None:
        filename = str(packet.get("filename", "arquivo")).replace("/", "_").replace("\\", "_")
        data = packet.get("data")
        if not isinstance(data, str):
            self._send_to(
                client.sock,
                {
                    "type": "error",
                    "timestamp": self._timestamp(),
                    "message": "invalid file",
                },
            )
            return

        self._broadcast(
            {
                "type": "file",
                "timestamp": self._timestamp(),
                "from": client.username,
                "filename": filename,
                "data": data,
            },
            exclude=client.sock,
        )
        self._send_to(
            client.sock,
            {
                "type": "system",
                "timestamp": self._timestamp(),
                "message": f"File {filename} sent to connected users.",
            },
        )

    def _unique_username(self, requested: str) -> str:
        base = requested or "user"
        with self.clients_lock:
            existing = {client.username for client in self.clients.values()}

        if base not in existing:
            return base

        suffix = 2
        while f"{base}{suffix}" in existing:
            suffix += 1
        return f"{base}{suffix}"

    def _broadcast_system(self, message: str) -> None:
        self._broadcast(
            {
                "type": "system",
                "timestamp": self._timestamp(),
                "message": message,
            }
        )

    def _broadcast(self, packet: dict[str, Any], exclude: socket.socket | None = None) -> None:
        with self.clients_lock:
            sockets = [sock for sock in self.clients if sock is not exclude]

        failed_sockets: list[socket.socket] = []
        for sock in sockets:
            try:
                send_packet(sock, packet)
            except (ConnectionError, OSError, ProtocolError):
                failed_sockets.append(sock)

        for sock in failed_sockets:
            with self.clients_lock:
                client = self.clients.get(sock)
            if client is not None:
                self._remove_client(client)

    def _send_to(self, sock: socket.socket, packet: dict[str, Any]) -> None:
        try:
            send_packet(sock, packet)
        except (ConnectionError, OSError, ProtocolError):
            with self.clients_lock:
                client = self.clients.get(sock)
            if client is not None:
                self._remove_client(client)

    def _remove_client(self, client: Client) -> None:
        removed = False
        with self.clients_lock:
            if client.sock in self.clients:
                del self.clients[client.sock]
                removed = True

        self._safe_close(client.sock)
        if removed:
            print(f"{client.username} disconnected")
            self._broadcast_system(f"{client.username} left the chat.")

    def _close_all_clients(self) -> None:
        with self.clients_lock:
            sockets = list(self.clients)
            self.clients.clear()

        for sock in sockets:
            self._safe_close(sock)

    @staticmethod
    def _safe_close(sock: socket.socket) -> None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAN TCP chat server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="listening interface; default: 0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="TCP port; default: 5050")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ChatServer(args.host, args.port).start()


if __name__ == "__main__":
    main()
