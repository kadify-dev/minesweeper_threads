import logging


def setup_logger(name: str, log_file: str = "log.log") -> logging.Logger:
    """
    Настройка логгера.

    :param name: Имя логгера (обычно __name__).
    :param log_file: Имя файла для записи логов.
    :return: Настроенный логгер.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)13s - %(levelname)8s - %(message)s"
    )

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)

    return logger
