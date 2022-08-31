import abc
import typing as t
from pathlib import Path


class BuildSystem(abc.ABC):
    name: str

    def __init__(self, execution_root_path: Path):
        self._root_path: Path = execution_root_path

    @abc.abstractmethod
    def build(self, force_rebuild: bool = False):
        raise NotImplementedError

    @abc.abstractmethod
    def purge(self):
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, command: str):
        raise NotImplementedError

    @abc.abstractmethod
    def interactive(self):
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(self):
        raise NotImplementedError


class Linter(abc.ABC):
    name: str
    parallel_run: bool

    def __init__(self, path: Path, args: t.Optional[t.List[str]] = None):
        if args is None:
            args = []
        self._path = path
        self._args = args

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError

    @abc.abstractmethod
    def check(self):
        raise NotImplementedError
