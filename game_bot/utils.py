import codecs
import logging
import sys


def new_logger(name: str, filepath: str=None, console_logger:bool=True, file_logger: bool=True):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if console_logger and not [handler for handler in logger.handlers if type(handler) == logging.StreamHandler]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file_logger and filepath and \
            not [handler for handler in logger.handlers if type(handler) == logging.FileHandler]:
        file_handler = logging.FileHandler(filepath)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def read_file(filepath: str):
    with codecs.open(filepath, 'r', 'utf-8') as file_:
        return file_.read()


def write_file(filepath: str, string: str):
    with codecs.open(filepath, 'w', 'utf-8') as file_:
        return file_.write(string)
