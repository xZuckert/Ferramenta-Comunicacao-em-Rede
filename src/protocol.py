# Protocolo JSON com prefixo de comprimento usado pelo aplicativo de bate-papo em rede local (LAN).

# O TCP é um fluxo de bytes, portanto, não preserva os limites das mensagens em nível de aplicativo.
# Este módulo adiciona uma pequena camada de enquadramento: quatro bytes contendo o comprimento da carga útil seguidos
# por um objeto JSON UTF-8.


from __future__ import annotations

import json
import socket
import struct
from typing import Any


HEADER_SIZE = 4
MAX_PACKET_SIZE = 64 * 1024 * 1024


class ProtocolError(ConnectionError):
    """Gerada quando o par remoto envia um quadro de protocolo inválido."""

def send_packet(sock: socket.socket, packet: dict[str, Any]) -> None:
    # Envia um dicionário como um pacote JSON com o length-prefixed.

    payload = json.dumps(packet, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_PACKET_SIZE:
        raise ProtocolError("packet exceeds the configured maximum size")

    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def recv_packet(sock: socket.socket) -> dict[str, Any]:
    # Recebe um pacote JSON completo com length-prefixed.

    header = _recv_exact(sock, HEADER_SIZE)
    payload_size = struct.unpack("!I", header)[0]
    if payload_size <= 0 or payload_size > MAX_PACKET_SIZE:
        raise ProtocolError(f"invalid packet size: {payload_size}")

    payload = _recv_exact(sock, payload_size)
    try:
        packet = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON payload") from exc

    if not isinstance(packet, dict):
        raise ProtocolError("packet must be a JSON object")
    return packet


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size

    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ProtocolError("connection closed by peer")
        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)
