import logging
import subprocess  # nosec B404
import typing as t
from pathlib import Path

from py_mono_build.interfaces.base_class import Linter


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Radon.

tflint
terrascan
"""

BLACK = "\x1b[30m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
WHITE = "\x1b[37m"
RESET = "\x1b[0m"


def run(linter: str, directory: Path, args: t.List[str]) -> int:
    log_format = "\n" + "#" * 20 + "  {}  " + "#" * 20 + "\n"

    logger.debug("Running %s: %s", linter, args)

    logs = log_format.format(linter + " start")

    process = subprocess.Popen(  # nosec B603
        args,
        cwd=directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout_data, stderr_data = process.communicate()

    if process.returncode != 0:
        logs += RED
    else:
        logs += GREEN

    logs += stdout_data.decode("utf-8")
    logs += stderr_data.decode("utf-8")

    logger.debug("%s return code: %s", linter, process.returncode)

    logs += RESET
    logs += log_format.format(linter + " end")

    logger.info(logs)
    return process.returncode


class Bandit(Linter):
    name: str = "bandit"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "bandit",
            "-r",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class Black(Linter):
    name: str = "black"
    parallel_run: bool = False

    def run(self):
        directory = self._path.resolve()
        args = [
            "black",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        directory = self._path.resolve()
        args = [
            "black",
            "--check",
            directory,
            *self._args,
        ]
        return run(self.name + " check", directory, args)


class DocStringFormatter(Linter):
    name: str = "docstring_formatter"
    parallel_run: bool = False

    def run(self):
        directory = self._path.resolve()
        args = [
            "pydocstringformatter",
            "-w",
            directory,
            *self._args,
        ]

        return run(self.name, directory, args)

    def check(self):
        directory = self._path.resolve()
        args = [
            "pydocstringformatter",
            directory,
            *self._args,
        ]

        run(self.name + " check", directory, args)


class Flake8(Linter):
    name: str = "flake8"
    parallel_run: bool = False

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        no_max_comp = True
        no_max_line = True
        if args is None:
            args = []

        for arg in args:
            if "--max-complexity" in arg:
                no_max_comp = False
            if "--max-line-length" in arg:
                no_max_line = False

        if no_max_comp is True:
            args.append("--max-complexity=10")
        if no_max_line is True:
            args.append("--max-line-length=120")

        args.append("--ignore=E203")

        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "flake8",
            directory,
            *self._args,
        ]

        return run(self.name, directory, args)

    def check(self):
        self.run()


class ISort(Linter):
    name: str = "isort"
    parallel_run: bool = False

    def run(self):
        directory = self._path.resolve()
        args = [
            "isort",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        directory = self._path.resolve()
        args = [
            "isort",
            "-c",
            directory,
            *self._args,
        ]
        return run(self.name + " check", directory, args)


class Mccabe(Linter):
    """
    Flake8 runs Mccabe.

    Only use this if you do not also run Flake8
    """

    name: str = "mccabe"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "python",
            "-m",
            "mccabe",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        self.run()


class Mypy(Linter):
    name: str = "mypy"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "mypy",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class Pydocstyle(Linter):
    name: str = "pydocstyle"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "pydocstyle",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class Pyflakes(Linter):
    """
    Flake8 runs pyflakes.

    Only use this if you do not also run Flake8
    """

    name: str = "pyflakes"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "pyflakes",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class Pylint(Linter):
    name: str = "pylint"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "pylint",
            directory,
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class TFSec(Linter):
    name: str = "tfsec"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        print(directory)
        args = [
            "docker",
            "run",
            "--rm",
            "-it",
            "-v",
            f"{directory}:/src",
            "aquasec/tfsec",
            "/src",
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class CheckOV(Linter):
    name: str = "checkov"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "docker",
            "run",
            "--tty",
            "--rm",
            "--volume",
            f"{directory}:/tf",
            "--workdir",
            "/tf",
            "bridgecrew/checkov",
            "--directory",
            "/tf",
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class Terrascan(Linter):
    name: str = "terrascan"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{directory}:/iac",
            "--workdir",
            "/iac",
            "tenable/terrascan",
            "scan",
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()


class TFLint(Linter):
    name: str = "tflint"
    parallel_run: bool = True

    def run(self):
        directory = self._path.resolve()
        args = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{directory}:/data",
            "-t",
            "ghcr.io/terraform-linters/tflint",
            *self._args,
        ]
        return run(self.name, directory, args)

    def check(self):
        return self.run()
