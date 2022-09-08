"""The system backend takes the goals instructions and runs them on the local system."""
import subprocess  # nosec B404
import typing as t

from py_mono_tools.backends.interface import Backend
from py_mono_tools.config import consts


class System(Backend):
    """Class to interact with the local system."""

    name: str = "system"

    def build(self, force_rebuild: bool = False):
        """Will do nothing for the system backend."""

    def purge(self):
        """Will do nothing for the system backend."""

    def run(self, args: t.List[str]):
        """Will run a command on the local system."""
        with subprocess.Popen(  # nosec B603
            args,
            cwd=consts.EXECUTED_FROM,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:

            stdout_data, stderr_data = process.communicate()
        return process.returncode, stderr_data.decode("utf-8") + stdout_data.decode("utf-8")

    def interactive(self):
        """Will do nothing for the system backend."""

    def shutdown(self):
        """Will do nothing for the system backend."""
