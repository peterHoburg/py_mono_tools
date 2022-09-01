import logging
import os
import pathlib


class Consts:
    EXECUTED_FROM: pathlib.Path = pathlib.Path(os.getcwd())
    CURRENT_BACKEND = None
    BACKENDS = None
    CONF = None


consts = Consts()

BLACK = "\x1b[30m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
WHITE = "\x1b[37m"
GRAY = "\x1b[38m"
RESET = "\x1b[0m"

FORMAT = "%(name)s-(%(filename)s:%(lineno)d)(%(process)d:%(thread)d) - %(levelname)s - %(asctime)s - %(message)s "


class ColorFormatting(logging.Formatter):
    FORMATS = {
        logging.DEBUG: GRAY + FORMAT + RESET,
        logging.INFO: GRAY + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: RED + FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("PMB")
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
stream.setFormatter(ColorFormatting())
logger.addHandler(stream)
