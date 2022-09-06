"""Contains the interfaces that goals will implement."""
import abc
import typing as t


class Linter(abc.ABC):
    """The interface that all linters will implement."""

    name: str
    parallel_run: bool
    weight: int = 0

    def __init__(self, args: t.Optional[t.List[str]] = None):
        """Will initialize the linter.

        Args are passed through to the linter.
        """
        if args is None:
            args = []
        self._args = args

    @abc.abstractmethod
    def run(self):
        """Will run the linter.

        Depending on the linter this may have side effects
        """
        raise NotImplementedError

    @abc.abstractmethod
    def check(self):
        """Will run the linter in check mode.This should NEVER change any files."""
        raise NotImplementedError
