import abc
import typing as t
from pathlib import Path


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
