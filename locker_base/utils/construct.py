from os.path import join
from typing import Iterable
import logging
from logging import handlers
import os


def construct_path(*args) -> str:
    path_name = ""
    for a in args:
        path_name = join(path_name, a)
    return path_name


def construct_handler(*, file_path, level: int = logging.INFO, max_bytes: int = 500000, backup_count: int = 10, formatter: logging.Formatter = None):
    filepath, _ = os.path.split(file_path)
    os.makedirs(filepath, exist_ok=True)
    f = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s") if not formatter else formatter
    logHandler = handlers.RotatingFileHandler(
        file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    logHandler.setLevel(level)
    logHandler.setFormatter(f)
    return logHandler


def construct_logger(*, file_path, level: int = logging.INFO, max_bytes: int = 500000, backup_count: int = 10, formatter: logging.Formatter = None):

    filepath, filename = os.path.split(file_path)
    os.makedirs(filepath, exist_ok=True)
    name = os.path.splitext(filename)[0]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # log formatter
    logHandler = construct_handler(file_path=file_path, level=level, max_bytes=max_bytes, backup_count=backup_count, formatter=formatter)

    # fixes bug when bot restarted but log file retained loghandler. this will remove any handlers it already had and replace with new ones initialized above
    for hdlr in list(logger.handlers):
        logger.removeHandler(hdlr)
    logger.addHandler(logHandler)

    return logger
