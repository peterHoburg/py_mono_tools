import subprocess
import typing as t
from pathlib import Path

from py_mono_build.interfaces.base_class import Linter


class Black(Linter):
    name: str = "black"
    parallel_run: bool = False

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "black",
            directory,
            *self._args,
        ]

        black_process = subprocess.Popen(args, cwd=directory)
        black_process.communicate()

        return black_process.returncode

    def check(self):
        directory = self._path.resolve()
        args = [
            "black",
            "--check",
            directory,
            *self._args,
        ]

        black_process = subprocess.Popen(args, cwd=directory)
        black_process.communicate()

        return black_process.returncode
