"""Store all the config/const data other files need."""
import logging
import os
import pathlib
import typing as t

from py_mono_tools.goals.interface import Linter


if t.TYPE_CHECKING:
    from py_mono_tools.backends.interface import Backend


# pylint: disable=too-few-public-methods
class Consts:
    """Used to store some "consts" that will be set at CLI runtime, then used in other modules."""

    EXECUTED_FROM: pathlib.Path = pathlib.Path(os.getcwd())  # pylint: disable=invalid-name
    CURRENT_BACKEND: t.Optional["Backend"] = None  # pylint: disable=invalid-name
    BACKENDS: t.Optional[t.Dict[str, t.Type["Backend"]]] = None  # pylint: disable=invalid-name
    CONF = None  # pylint: disable=invalid-name
    ALL_LINTERS: t.List[Linter] = []
    ALL_LINTER_NAMES: t.List[str] = []


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
    """Used to colorize the log output."""

    FORMATS = {
        logging.DEBUG: GRAY + FORMAT + RESET,
        logging.INFO: GRAY + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: RED + FORMAT + RESET,
    }

    def format(self, record):
        """Add formatting to the log output."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("PMT")
logger.setLevel(logging.INFO)

stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
stream.setFormatter(ColorFormatting())
logger.addHandler(stream)
