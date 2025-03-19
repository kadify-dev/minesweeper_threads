import socket
from threading import Thread
from typing import Any

from app.server.game_logic import Field, Player
from app.shared.config import settings
from app.shared.logger import setup_logger
from app.shared.network import receive, send

logger = setup_logger(__name__)


class Server:
    def __init__(self, host=settings.HOST, port=settings.PORT):
        self.HOST = host
        self.PORT = port
        self.players: list[Player] = []
        self.fields: list[Field] = [Field(), Field()]

    def __enter__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(2)
        logger.info("Сервер запущен на %s:%s", self.HOST, self.PORT)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for player in self.players:
            player.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        logger.info("Сервер остановлен.")

    def accept_players(self):
        logger.info("Ожидание подключения игроков")

        while len(self.players) < 2:
            client_socket, client_address = self.server_socket.accept()
            logger.info("Игрок подключился: %s", client_address)

            self.players.append(
                Player(len(self.players), client_socket, client_address)
            )
            logger.debug("Игрок создан: id=%s", len(self.players) - 1)
        logger.info("Два игрока подключены, игра начинается.")

    def handle_client_message(
        self, data: dict[str, Any], player: Player
    ) -> dict[str, Any]:
        if data["stage"] == 1:
            self.fields[1 - player.id].place_mine(
                data["move"]["x"] - 1, data["move"]["y"] - 1
            )
            player.count_place_mine += 1
            return {
                "stage": 1,
                "message": "Введите координаты (x y): ",
                "cell": {
                    "x": data["move"]["x"] - 1,
                    "y": data["move"]["y"] - 1,
                    "info": {
                        "is_open": True,
                        "is_mine": True,
                    },
                },
            }
        elif data["stage"] == 2:
            x, y = data["move"]["x"] - 1, data["move"]["y"] - 1
            self.fields[player.id].open_cell(x, y)

            if self.fields[player.id].grid[x][y].is_mine:
                player.count_detonated_mine += 1

            message = (
                "Вы попали на мину."
                if self.fields[player.id].grid[x][y].is_mine
                else "Вы увернулись."
            )

            return {
                "stage": 2,
                "message": message,
                "cell": {
                    "x": x,
                    "y": y,
                    "info": {
                        "is_open": True,
                        "is_mine": self.fields[player.id].grid[x][y].is_mine,
                    },
                },
            }

    def is_valid_cell(self, data: dict[str, Any], player: Player) -> bool:
        x, y = data["move"]["x"], data["move"]["y"]
        stage = data["stage"]
        logger.debug("Проверка координат x=%s, y=%s", x, y)
        if 1 <= x <= 5 and 1 <= y <= 5:
            if (
                stage == 1
                and self.fields[1 - player.id].grid[x - 1][y - 1].is_mine is False
            ):
                logger.debug("Координаты x=%s, y=%s допустимы", x, y)
                return True
            if (
                stage == 2
                and self.fields[player.id].grid[x - 1][y - 1].is_open is False
            ):
                logger.debug("Координаты x=%s, y=%s допустимы", x, y)
                return True
        logger.warning("Координаты x=%s, y=%s выходят за допустимые пределы", x, y)
        return False

    def place_mines(self, player: Player):
        logger.info("Игрок %s ставит мины", player.id)

        for _ in range(settings.MINE_COUNT):
            while True:
                message = {
                    "action": True,
                    "message": "Введите координаты (x y): ",
                    "stage": 1,
                }
                send(player.client_socket, message)
                data = receive(player.client_socket)

                if self.is_valid_cell(data, player):
                    break

            data = self.handle_client_message(data, player)

            send(player.client_socket, data)
            data = receive(player.client_socket)

    def send_start_game_data(self, player: Player):
        message = {
            "grid": self.fields[1 - player.id].to_dict()["grid"],
        }
        send(player.client_socket, message)
        data = receive(player.client_socket)

    def open_cell(self, player: Player):
        logger.info("Игрок %s открывает ячейку", player.id)

        while True:
            message = {
                "action": True,
                "message": "Введите координаты (x y): ",
                "stage": 2,
            }
            send(player.client_socket, message)
            data = receive(player.client_socket)

            if self.is_valid_cell(data, player):
                break

        data = self.handle_client_message(data, player)

        send(player.client_socket, data)
        data = receive(player.client_socket)

    def close_cell(self, player: Player):
        self.fields[player.id].close_all_cell()

        message = {
            "grid": self.fields[player.id].to_dict()["grid"],
        }
        send(player.client_socket, message)
        data = receive(player.client_socket)

    def check_lose(self, player: Player):
        return player.count_detonated_mine == 5

    def process_game(self, player: Player):
        for count_move in range(settings.FIELD_SIZE * settings.FIELD_SIZE):
            self.open_cell(player)
            if self.check_lose(player):
                player.is_lose = True
                player.count_move = count_move
                return

    def send_end_game_data(self, player1: Player, player2: Player):

        if player1.count_move > player2.count_move:
            message_player1 = "победа"
            message_player2 = "проигрыш"
        elif player1.count_move < player2.count_move:
            message_player1 = "проигрыш"
            message_player2 = "победа"
        else:
            message_player1 = "ничья"
            message_player2 = "ничья"

        send(player1.client_socket, {"message": message_player1})
        data = receive(player1.client_socket)

        send(player2.client_socket, {"message": message_player2})
        data = receive(player2.client_socket)

    def thread_game(self, target):
        threads: list[Thread] = []
        for player in self.players:
            threads.append(Thread(target=target, args=(player,), daemon=True))

        threads[0].start()
        threads[1].start()

        threads[0].join()
        threads[1].join()

    def run(self):
        self.accept_players()

        for player in self.players:
            self.send_start_game_data(player)

        self.thread_game(self.place_mines)

        for player in self.players:
            self.close_cell(player)

        self.thread_game(self.process_game)

        self.send_end_game_data(self.players[0], self.players[1])
