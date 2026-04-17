# Descoberta de broadcast UDP para o servidor de chat da LAN.

# O próprio chat continua a usar TCP. O UDP é usado apenas para encontrar automaticamente o servidor TCP na rede local.


from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import dataclass


DISCOVERY_PORT = 5052
DISCOVERY_MAGIC = "CHAT_TCP_LAN_DISCOVERY_V1"
DISCOVER_MESSAGE = "DISCOVER"
OFFER_MESSAGE = "OFFER"


@dataclass(frozen=True)
class ServerOffer:
    host: str
    port: int
    name: str


class DiscoveryResponder:
    # Responde a solicitações de descoberta UDP com o endereço do servidor TCP local.

    def __init__(
        self,
        chat_port: int,
        discovery_port: int = DISCOVERY_PORT,
        server_name: str = "Chat TCP LAN",
    ) -> None:
        self.chat_port = chat_port
        self.discovery_port = discovery_port
        self.server_name = server_name
        self.running = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        self.running.set()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running.clear()

    def _serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_sock.bind(("", self.discovery_port))
            udp_sock.settimeout(1.0)

            while self.running.is_set():
                try:
                    data, address = udp_sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except OSError:
                    break

                request = _decode_message(data)
                if request.get("magic") != DISCOVERY_MAGIC:
                    continue
                if request.get("type") != DISCOVER_MESSAGE:
                    continue

                response = _encode_message(
                    {
                        "magic": DISCOVERY_MAGIC,
                        "type": OFFER_MESSAGE,
                        "port": self.chat_port,
                        "name": self.server_name,
                    }
                )
                udp_sock.sendto(response, address)


def discover_server(
    discovery_port: int = DISCOVERY_PORT,
    timeout: float = 2.0,
    broadcast_address: str = "255.255.255.255",
) -> ServerOffer | None:
    # Transmita uma solicitação de descoberta e retorne a primeira oferta de servidor válida.

    deadline = time.monotonic() + timeout
    request = _encode_message({"magic": DISCOVERY_MAGIC, "type": DISCOVER_MESSAGE})

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_sock.settimeout(0.25)
        udp_sock.sendto(request, (broadcast_address, discovery_port))

        while time.monotonic() < deadline:
            try:
                data, address = udp_sock.recvfrom(4096)
            except socket.timeout:
                continue

            response = _decode_message(data)
            if response.get("magic") != DISCOVERY_MAGIC:
                continue
            if response.get("type") != OFFER_MESSAGE:
                continue

            port = response.get("port")
            if not isinstance(port, int):
                continue

            name = response.get("name")
            if not isinstance(name, str):
                name = "Chat TCP LAN"

            return ServerOffer(host=address[0], port=port, name=name)

    return None


def _encode_message(message: dict[str, object]) -> bytes:
    return json.dumps(message, ensure_ascii=False).encode("utf-8")


def _decode_message(data: bytes) -> dict[str, object]:
    try:
        message = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}

    if not isinstance(message, dict):
        return {}
    return message
