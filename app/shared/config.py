from dataclasses import dataclass


@dataclass
class Settings:
    HOST: str = "127.0.0.1"
    PORT: int = 65432

    FIELD_SIZE: int = 5
    MINE_COUNT: int = 5


settings = Settings()
