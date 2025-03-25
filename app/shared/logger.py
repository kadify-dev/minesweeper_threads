import logging


def setup_logger(name: str, log_file: str = "log.log") -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)

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
