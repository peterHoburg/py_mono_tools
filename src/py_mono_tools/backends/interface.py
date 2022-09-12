"""Contains the interfaces that backends will implement."""
import abc
import typing as t


# pylint: disable=R0801
class Backend(abc.ABC):
    """The interface that all backends will implement."""

    name: str

    @abc.abstractmethod
    def build(self, force_rebuild: bool = False):
        """Will run any build jobs that are needed for the backend."""
        raise NotImplementedError

    @abc.abstractmethod
    def purge(self):
        """Will remove any data written by the backend."""
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, args: t.List[str], workdir: str) -> t.Tuple[int, str]:
        """Will run a command in the backend."""
        raise NotImplementedError

    @abc.abstractmethod
    def interactive(self):
        """Will drop the user into an interactive shell."""
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(self):
        """Will shut down any instances of the backend."""
        raise NotImplementedError
