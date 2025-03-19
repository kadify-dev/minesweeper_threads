import json
import socket
from typing import Any

from app.shared.logger import setup_logger

logger = setup_logger(__name__)


def send(client_socket: socket, data: dict[str, Any]) -> None:
    """
    Отправляет данные по сокету в формате JSON. Принимает только словарь.

    :param client_socket: Сокет для отправки данных.
    :param data: Данные для отправки (только словарь).
    """

    if not isinstance(data, dict):
        logger.error("Ожидается словарь, получен %s", type(data))
        raise TypeError

    try:
        # Сериализуем данные в JSON
        json_data = json.dumps(data).encode("utf-8")

        # Отправляем размер данных (4 байта)
        size = len(json_data)
        client_socket.sendall(size.to_bytes(4, byteorder="big"))

        # Отправляем сами данные
        client_socket.sendall(json_data)

        logger.info("Отправлено %s байт данных: %s", size, data)
    except Exception as e:
        logger.error("Ошибка при отправке данных: %s", e)
        raise


def receive(client_socket: socket, buffer_size: int = 1024) -> dict[str, Any]:
    """
    Принимает данные по сокету в формате JSON. Возвращает только словарь.

    :param client_socket: Сокет для приема данных.
    :param buffer_size: Размер буфера для приема данных.
    :return: Десериализованные данные (словарь).
    """
    try:
        # Читаем размер данных (первые 4 байта)
        size_data = client_socket.recv(4)
        if not size_data:
            raise ValueError("Соединение закрыто")

        # Преобразуем размер данных в число
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
