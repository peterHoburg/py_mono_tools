import pathlib
import typing as t

import pytest

from py_mono_tools.utils.utils import example_repo_path, run_command_in_tty


@pytest.fixture(scope="class")
def vagrant(request) -> t.Iterator[pathlib.Path]:
    repo = request.param
    cwd = example_repo_path(repo)

    status_commands = "vagrant status"
    up_commands = "vagrant up --provision"
    halt_commands = "vagrant halt"

    returncode, output = run_command_in_tty(status_commands, cwd=cwd)
    if b"poweroff" in output or b"The environment has not yet been created" in output:
        returncode, output = run_command_in_tty(up_commands, cwd=cwd)
        if returncode != 0:
            raise RuntimeError("vagrant up failed with output: %s", output)

    try:
        yield cwd
    finally:
        run_command_in_tty(halt_commands, cwd=cwd)
