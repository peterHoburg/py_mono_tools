import subprocess  # nosec B404
import os
import pty
import typing as t
import pathlib


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


def vagrant(commands: str, cwd: pathlib.Path = None) -> t.Tuple[int, bytes]:
    up_commands = "vagrant up --provision"
    run_commands = f'vagrant ssh default --command "cd /vagrant; {commands}"'

    returncode, output = run_command_in_tty(up_commands, cwd=cwd)
    if returncode != 0:
        raise RuntimeError("vagrant up failed with output: %s", output)

    returncode, output = run_command_in_tty(run_commands, cwd=cwd)
    return returncode, output


def example_repo_path(repo: str) -> pathlib.Path:
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    example_repo = project_root.joinpath("example_repos")
    cwd = example_repo.joinpath(repo)

    return cwd