import json
import socket
from typing import Any

from app.shared.logger import setup_logger

logger = setup_logger(__name__)


def send(client_socket: socket, data: dict[str, Any]) -> None:

    if not isinstance(data, dict):
        logger.error("Ожидается словарь, получен %s", type(data))
        raise TypeError

    try:
        json_data = json.dumps(data).encode("utf-8")

        size = len(json_data)
        client_socket.sendall(size.to_bytes(4, byteorder="big"))

        client_socket.sendall(json_data)

        logger.info("Отправлено %s байт данных: %s", size, data)
    except Exception as e:
        logger.error("Ошибка при отправке данных: %s", e)
        raise


def receive(client_socket: socket, buffer_size: int = 1024) -> dict[str, Any]:
    try:
        size_data = client_socket.recv(4)
        if not size_data:
            raise ValueError("Соединение закрыто")

        size = int.from_bytes(size_data, byteorder="big")

        received_data = b""
        while len(received_data) < size:
            part = client_socket.recv(min(buffer_size, size - len(received_data)))
            logger.debug("Принят чанк: %s", part)
            if not part:
                break
            received_data += part

        data = json.loads(received_data.decode("utf-8"))

        if not isinstance(data, dict):
            logger.error("Ожидается словарь, получен %s", type(data))
            raise TypeError

        logger.info("Принято %s байт данных: %s", len(received_data), data)
        return data
    except Exception as e:
        logger.error("Ошибка при приеме данных: %s", e)
        raise
