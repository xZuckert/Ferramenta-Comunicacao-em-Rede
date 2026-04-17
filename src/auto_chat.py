# Iniciador automático de bate-papo em rede local (LAN).

# Exemplo de uso:
# python3 auto_chat.py --username maria

# O iniciador primeiro tenta descobrir um servidor de bate-papo existente na rede local.
# Se nenhum for encontrado, ele inicia um servidor TCP local e o anuncia com
# descoberta por broadcast UDP.


from __future__ import annotations

import argparse
import random
import socket
import sys
import threading
import time

from client import ChatClient
from discovery import DISCOVERY_PORT, DiscoveryResponder, discover_server
from server import DEFAULT_PORT, ChatServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAN TCP chat with automatic local-network connection")
    parser.add_argument("--username", "-u", required=True, help="name shown in the chat")
    parser.add_argument("--chat-port", type=int, default=DEFAULT_PORT, help="TCP chat port; default: 5050")
    parser.add_argument(
        "--discovery-port",
        type=int,
        default=DISCOVERY_PORT,
        help="UDP port used for automatic discovery; default: 5052",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="seconds spent looking for an existing room; default: 2.0",
    )
    parser.add_argument(
        "--server-name",
        default="Chat TCP LAN",
        help="name announced when this computer hosts the room",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Searching for a chat room on the local network...")
    offer = discover_server(args.discovery_port, args.timeout)
    if offer is None:
        # Reduces the chance of two computers becoming server at the same time.
        time.sleep(random.uniform(0.2, 0.8))
        offer = discover_server(args.discovery_port, 0.8)

    if offer is not None:
        print(f"Room found: {offer.name} at {offer.host}:{offer.port}")
        _start_client(offer.host, offer.port, args.username)
        return

    print("No room found. This computer will host the room.")
    server = ChatServer("0.0.0.0", args.chat_port)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    responder = DiscoveryResponder(args.chat_port, args.discovery_port, args.server_name)
    responder.start()

    if not _wait_until_tcp_ready("127.0.0.1", args.chat_port, timeout=3.0):
        responder.stop()
        print("Unable to start the local server.")
        sys.exit(1)

    try:
        _start_client("127.0.0.1", args.chat_port, args.username)
    finally:
        responder.stop()
        server.running.clear()


def _start_client(host: str, port: int, username: str) -> None:
    try:
        ChatClient(host, port, username).start()
    except ConnectionRefusedError:
        print("Connection refused. The room may have been closed.")
        sys.exit(1)
    except OSError as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)


def _wait_until_tcp_ready(host: str, port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.1)
    return False


if __name__ == "__main__":
    main()
