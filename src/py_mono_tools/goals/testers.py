"""Contains all the implemented testers."""
import typing as t

from py_mono_tools.config import consts, GREEN, logger, RED, RESET
from py_mono_tools.goals.interface import Language, Tester


def _run(tester: str, args: t.List[str], workdir=None) -> t.Tuple[str, int]:
    log_format = "\n" + "#" * 20 + "  {}  " + "#" * 20 + "\n"
    logs = ""

    logger.debug("Running %s: %s", tester, args)
    if len(args) > 0 and "docker" == args[0] and consts.CURRENT_BACKEND.name == "docker":  # type: ignore
        logger.debug("Bypassing docker backend for system backend. Tester: %s", tester)
        return_code, returned_logs = consts.BACKENDS["system"]().run(args, workdir=workdir)  # type: ignore
    else:
        return_code, returned_logs = consts.CURRENT_BACKEND.run(args, workdir=workdir)  # type: ignore
    logger.debug("%s return code: %s", tester, return_code)

    color = GREEN if return_code == 0 else RED
    logs += color
    logs += log_format.format(tester + " start")
    logs = logs + returned_logs
    logs += color
    logs += log_format.format(tester + " end")
    logs += RESET

    return logs, return_code


class PytestTester(Tester):  # pylint: disable=too-few-public-methods
    """Pytest tester."""

    name = "pytest"
    language = Language.PYTHON

    def run(self):
        """Will Run pytest.

        Changes working dir to the workdir passed to the class init.
        """
        args = [
            "pytest",
        ]

        return _run(self.name, args, workdir=self._test_dir)
