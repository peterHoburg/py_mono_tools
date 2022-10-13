import subprocess  # nosec B404
import os
import pty
import typing as t
import pathlib
import pytest


def run_command_in_tty(command: str, cwd: pathlib.Path) -> t.Tuple[int, bytes]:
    command_fd, worker_fd = pty.openpty()

    p = subprocess.Popen(
        [command],
        preexec_fn=os.setsid,
        stdin=worker_fd,
        stdout=worker_fd,
        stderr=worker_fd,
        universal_newlines=True,
        shell=True,
        cwd=cwd,
    )
    returncode = p.wait()
    os.close(worker_fd)

    output = []
    while True:
        try:
            data = os.read(command_fd, 1024)
        except OSError:
            break
        if not data:
            break
        output.append(data)
    output = b"".join(output)
    return returncode, output


@pytest.fixture()
def vagrant(commands: str, cwd: pathlib.Path = None) -> t.Generator[t.Tuple[int, bytes]]:
    status_commands = "vagrant status"
    up_commands = "vagrant up --provision"
    run_commands = f'vagrant ssh default --command "cd /vagrant; {commands}"'
    halt_commands = "vagrant halt"

    returncode, output = run_command_in_tty(status_commands, cwd=cwd)

    if b"poweroff" in output:
        returncode, output = run_command_in_tty(up_commands, cwd=cwd)
        if returncode != 0:
            raise RuntimeError("vagrant up failed with output: %s", output)

    returncode, output = run_command_in_tty(run_commands, cwd=cwd)
    try:
        yield returncode, output
    except:
        run_command_in_tty(halt_commands, cwd=cwd)
        raise


def example_repo_path(repo: str) -> pathlib.Path:
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "src":
        project_root = project_root.parent
    project_root = project_root.parent
    example_repo = project_root.joinpath("example_repos")
    cwd = example_repo.joinpath(repo)

    return cwd
