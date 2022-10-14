import typing as t

import pydantic


class GoalOutput(pydantic.BaseModel):
    """Output of a goal."""

    name: str
    return_code: int
    output: bytes


class CliMachineOutput(pydantic.BaseModel):
    """Output returned when the machine output flag is set."""

    return_code: int
    all_outputs: bytes

    goals: t.List[GoalOutput]
