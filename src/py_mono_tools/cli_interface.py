import typing as t

import pydantic


class GoalOutput(pydantic.BaseModel):
    """Output of a goal."""

    name: str
    returncode: int
    output: bytes


class CliMachineOutput(pydantic.BaseModel):
    """Output returned when the machine output flag is set."""

    returncode: int
    all_outputs: bytes

    goals: t.List[GoalOutput]
