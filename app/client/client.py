import msvcrt
import os
import socket
from typing import Any

from app.shared.config import settings
from app.shared.logger import setup_logger
from app.shared.network import receive, send

logger = setup_logger(__name__)


class Client:
    def __init__(self, host=settings.HOST, port=settings.PORT) -> None:
        self.HOST = host
        self.PORT = port
        self.message = "Введите координаты (x y): "
        self.grid: list[list[dict[str, Any]]] | None = None

    def __enter__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.HOST, self.PORT))
        logger.info(f"Клиент запущен на {self.HOST}:{self.PORT}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client_socket:
            self.client_socket.close()
        logger.info("Клиент остановлен")

    def handle_server_message(self, data: dict[str, Any]) -> dict[str, Any]:

        self.clear_input_buffer()

        if "grid" in data:
            self.grid = data["grid"]

        if "cell" in data:
            x = data["cell"]["x"]
            y = data["cell"]["y"]
            self.grid[x][y] = data["cell"]["info"]

        if "message" in data:
            self.message = data["message"]

        if "action" in data:
            while True:
                try:
                    x, y = map(int, input().split())
                    break
                except Exception as e:
                    logger.error("Введены некорректные данные: %s", e)

            return {
                "move": {"x": x, "y": y},
                "stage": data["stage"],
            }

        self.clear_console()
        self.draw_field()

        return {"message": "OK"}

    def draw_field(self):
        logger.info("Отрисовка игрового поля...")
        if self.grid is None:
            return
        print("+----" * len(self.grid[0]) + "+")
        for row in self.grid:
            print("| ", end="")
            for cell in row:
                if not cell["is_open"]:
                    print("## | ", end="")
                elif cell["is_mine"]:
                    print("💣 | ", end="")
                else:
                    print("   | ", end="")
            print()
            print("+----" * len(row) + "+")

        print(self.message)

    def clear_console(self):
        if os.name == "nt":
            os.system("cls")

    def clear_input_buffer(self):
        if os.name == "nt":
            while msvcrt.kbhit():
                msvcrt.getch()

    def run(self):
        while True:

            data = receive(self.client_socket)

            message = self.handle_server_message(data)

            send(self.client_socket, message)
