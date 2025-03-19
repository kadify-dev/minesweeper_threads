import socket

from app.shared.config import settings


class Cell:
    def __init__(self):
        self.is_open = True
        self.is_mine = False

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def place_mine(self):
        self.is_mine = True

    def to_dict(self):
        return {
            "is_open": self.is_open,
            "is_mine": self.is_mine,
        }


class Field:
    def __init__(self):
        self.grid = [
            [Cell() for _ in range(settings.FIELD_SIZE)]
            for _ in range(settings.FIELD_SIZE)
        ]

    def open_cell(self, x, y):
        self.grid[x][y].open()

    def close_cell(self, x, y):
        self.grid[x][y].close()

    def place_mine(self, x, y):
        self.grid[x][y].place_mine()

    def close_all_cell(self):
        for row in self.grid:
            for cell in row:
                cell.close()

    def to_dict(self):
        return {
            "grid": [[cell.to_dict() for cell in row] for row in self.grid],
        }


class Player:
    def __init__(self, id: int, client_socket: socket, client_address):
        self.id = id
        self.client_socket = client_socket
        self.client_address = client_address
        self.count_move = 0
        self.count_place_mine = 0
        self.count_detonated_mine = 0
        self.is_lose = False

    def to_dict(self):
        return {
            "id": self.id,
            "count_move": self.count_move,
            "count_place_mine": self.count_place_mine,
            "count_detonated_mine": self.count_detonated_mine,
        }
