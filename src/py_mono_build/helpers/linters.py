import logging
import subprocess
import typing as t
from pathlib import Path

from py_mono_build.interfaces.base_class import Linter


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

"""
Flake8
    pyflakes
    pycodestyle
    mccabe


pylint
pyflakes
pycodestyle

pydocstyle
pydocstringformatter

Bandit
mypy
mccabe
Radon
Black
Isort
"""
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
        logger.debug(f"Running black: {args}")

        black_process = subprocess.Popen(args, cwd=directory)
        black_process.communicate()

        logger.debug(f"Return code: {black_process.returncode}")

        return black_process.returncode

    def check(self):
        directory = self._path.resolve()
        args = [
            "black",
            "--check",
            directory,
            *self._args,
        ]

        logger.debug(f"Running check black: {args}")

        black_process = subprocess.Popen(args, cwd=directory)
        black_process.communicate()

        logger.debug(f"Return code: {black_process.returncode}")

        return black_process.returncode


class DocStringFormatter(Linter):
    name: str = "docstring_formatter"
    parallel_run: bool = False

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "pydocstringformatter",
            "-w",
            directory,
            *self._args,
        ]
        logger.debug(f"Running docstring_formatter: {args}")

        docstring_formatter_process = subprocess.Popen(args, cwd=directory)
        docstring_formatter_process.communicate()

        logger.debug(f"Return code: {docstring_formatter_process.returncode}")

        return docstring_formatter_process.returncode

    def check(self):
        directory = self._path.resolve()
        args = [
            "pydocstringformatter",
            directory,
            *self._args,
        ]

        logger.debug(f"Running check docstring_formatter: {args}")

        docstring_formatter_process = subprocess.Popen(args, cwd=directory)
        docstring_formatter_process.communicate()

        logger.debug(f"Return code: {docstring_formatter_process.returncode}")

        return docstring_formatter_process.returncode


class ISort(Linter):
    name: str = "isort"
    parallel_run: bool = False

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "isort",
            directory,
            *self._args,
        ]
        logger.debug(f"Running isort: {args}")

        isort_process = subprocess.Popen(args, cwd=directory)
        isort_process.communicate()

        logger.debug(f"Return code: {isort_process.returncode}")

        return isort_process.returncode

    def check(self):
        directory = self._path.resolve()
        args = [
            "isort",
            "-c",
            directory,
            *self._args,
        ]
        logger.debug(f"Running check isort: {args}")
        isort_process = subprocess.Popen(args, cwd=directory)
        isort_process.communicate()

        logger.debug(f"Return code: {isort_process.returncode}")

        return isort_process.returncode


class Mypy(Linter):
    name: str = "mypy"
    parallel_run: bool = True

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "mypy",
            directory,
            *self._args,
        ]
        logger.debug(f"Running mypy: {args}")

        mypy_process = subprocess.Popen(args, cwd=directory)
        mypy_process.communicate()

        logger.debug(f"Return code: {mypy_process.returncode}")

        return mypy_process.returncode

    def check(self):
        return self.run()


class Pydocstyle(Linter):
    name: str = "pydocstyle"
    parallel_run: bool = True

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "pydocstyle",
            directory,
            *self._args,
        ]
        logger.debug(f"Running pydocstyle: {args}")

        pydocstyle_process = subprocess.Popen(args, cwd=directory)
        pydocstyle_process.communicate()

        logger.debug(f"Return code: {pydocstyle_process.returncode}")

        return pydocstyle_process.returncode

    def check(self):
        return self.run()


class Pyflakes(Linter):
    name: str = "pyflakes"
    parallel_run: bool = True

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "pyflakes",
            directory,
            *self._args,
        ]
        logger.debug(f"Running pyflakes: {args}")

        pyflakes_process = subprocess.Popen(args, cwd=directory)
        pyflakes_process.communicate()

        logger.debug(f"Return code: {pyflakes_process.returncode}")

        return pyflakes_process.returncode

    def check(self):
        return self.run()


class Pylint(Linter):
    name: str = "pylint"
    parallel_run: bool = True

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "pylint",
            directory,
            *self._args,
        ]
        logger.debug(f"Running pylint: {args}")

        pylint_process = subprocess.Popen(args, cwd=directory)
        pylint_process.communicate()

        logger.debug(f"Return code: {pylint_process.returncode}")

        return pylint_process.returncode

    def check(self):
        return self.run()


class Bandit(Linter):
    name: str = "bandit"
    parallel_run: bool = True

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        super().__init__(path, args)

    def run(self):
        directory = self._path.resolve()
        args = [
            "bandit",
            "-r",
            directory,
            *self._args,
        ]
        logger.debug(f"Running bandit: {args}")

        bandit_process = subprocess.Popen(args, cwd=directory)
        bandit_process.communicate()

        logger.debug(f"Return code: {bandit_process.returncode}")

        return bandit_process.returncode

    def check(self):
        return self.run()
