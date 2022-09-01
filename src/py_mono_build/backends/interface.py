import abc
from pathlib import Path


class Backend(abc.ABC):
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
