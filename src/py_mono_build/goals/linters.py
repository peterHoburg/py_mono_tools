import typing as t

from py_mono_build.config import consts, GREEN, logger, RED, RESET
from py_mono_build.goals.interface import Linter


def _run(linter: str, args: t.List[str]) -> t.Tuple[str, int]:
    log_format = "\n" + "#" * 20 + "  {}  " + "#" * 20 + "\n"
    logs = ""

    logger.debug("Running %s: %s", linter, args)
    return_code, returned_logs = consts.CURRENT_BACKEND.run(args)  # type: ignore
    logger.debug("%s return code: %s", linter, return_code)

    color = GREEN if return_code == 0 else RED
    logs += color
    logs += log_format.format(linter + " start")
    logs = logs + returned_logs
    logs += color
    logs += log_format.format(linter + " end")
    logs += RESET

    return logs, return_code


class Bandit(Linter):
    name: str = "bandit"
    parallel_run: bool = True

    def run(self):
        args = [
            "bandit",
            "-r",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class Black(Linter):
    name: str = "black"
    parallel_run: bool = False

    def run(self):
        args = [
            "black",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        args = [
            "black",
            "--check",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name + " check", args)


class DocStringFormatter(Linter):
    name: str = "doc_string_formatter"
    parallel_run: bool = False

    def run(self):
        args = [
            "pydocstringformatter",
            "-w",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name, args)

    def check(self):
        args = [
            "pydocstringformatter",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        _run(self.name + " check", args)


class Flake8(Linter):
    name: str = "flake8"
    parallel_run: bool = False

    def __init__(self, args: t.Optional[t.List[str]] = None):
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

        super().__init__(args)

    def run(self):
        args = [
            "flake8",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name, args)

    def check(self):
        self.run()


class ISort(Linter):
    name: str = "isort"
    parallel_run: bool = False

    def run(self):
        args = [
            "isort",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        args = [
            "isort",
            "-c",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name + " check", args)


class Mccabe(Linter):
    """
    Flake8 runs Mccabe.

    Only use this if you do not also run Flake8
    """

    name: str = "mccabe"
    parallel_run: bool = True

    def run(self):
        args = [
            "python",
            "-m",
            "mccabe",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        self.run()


class Mypy(Linter):
    name: str = "mypy"
    parallel_run: bool = True

    def run(self):
        args = [
            "mypy",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class Pydocstyle(Linter):
    name: str = "pydocstyle"
    parallel_run: bool = True

    def run(self):
        args = [
            "pydocstyle",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

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
        args = [
            "pyflakes",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class Pylint(Linter):
    name: str = "pylint"
    parallel_run: bool = True

    def run(self):
        args = [
            "pylint",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class TFSec(Linter):
    name: str = "tfsec"
    parallel_run: bool = True

    def run(self):
        args = [
            "docker",
            "run",
            "--rm",
            "-it",
            "-v",
            f"{consts.EXECUTED_FROM}:/src",
            "aquasec/tfsec",
            "/src",
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class CheckOV(Linter):
    name: str = "checkov"
    parallel_run: bool = True

    def run(self):
        args = [
            "docker",
            "run",
            "--tty",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/tf",
            "--workdir",
            "/tf",
            "bridgecrew/checkov",
            "--directory",
            "/tf",
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class Terrascan(Linter):
    name: str = "terrascan"
    parallel_run: bool = True

    def run(self):
        args = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/iac",
            "--workdir",
            "/iac",
            "tenable/terrascan",
            "scan",
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()


class TFLint(Linter):
    name: str = "tflint"
    parallel_run: bool = True

    def run(self):
        args = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{consts.EXECUTED_FROM}:/data",
            "-t",
            "ghcr.io/terraform-linters/tflint",
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        return self.run()
