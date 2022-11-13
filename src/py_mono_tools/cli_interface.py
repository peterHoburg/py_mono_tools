"""Defines the outputs of the CLI in JSON."""
import typing as t

from pydantic import BaseModel  # pylint: disable=E0611


# pylint: disable=R0903
class GoalOutput(BaseModel):
    """Output of a goal."""

    name: str
    returncode: int
    output: bytes


# pylint: disable=R0903
class CliMachineOutput(BaseModel):
    """Output returned when the machine output flag is set."""

    returncode: int
    all_outputs: bytes

    goals: t.Dict[str, GoalOutput]
