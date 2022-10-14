"""The system backend takes the goals instructions and runs them on the local system."""
import pathlib
import subprocess  # nosec B404
import typing as t

from py_mono_tools.backends.interface import Backend
from py_mono_tools.config import consts, logger
from py_mono_tools.utils import run_command_in_tty


class System(Backend):
    """Class to interact with the local system."""

    name: str = "system"

    def build(self, force_rebuild: bool = False):
        """Will do nothing for the system backend."""

    def purge(self):
        """Will do nothing for the system backend."""

    def run(self, args: t.List[str], workdir: str = None) -> t.Tuple[int, bytes]:
        """Will run a command on the local system."""
        if workdir is not None:
            workdir = pathlib.Path(workdir).absolute()

        return run_command_in_tty(command=args, cwd=workdir or consts.EXECUTED_FROM)

    def interactive(self):
        """Will do nothing for the system backend."""

    def shutdown(self):
        """Will do nothing for the system backend."""
