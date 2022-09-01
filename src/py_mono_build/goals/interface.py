import abc
import typing as t


class Linter(abc.ABC):
    name: str
    parallel_run: bool

    def __init__(self, args: t.Optional[t.List[str]] = None):
        if args is None:
            args = []
        self._args = args

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError

    @abc.abstractmethod
    def check(self):
        raise NotImplementedError
