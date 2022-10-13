import os
import pathlib
import pty
import subprocess  # nosec B404
import typing as t


def _read(commands: t.List[str], cwd: str = None) -> t.Tuple[int, str]:
    command_fd, worker_fd = pty.openpty()

    p = subprocess.Popen(
        commands,
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


def vagrant(commands: str, cwd: str = None):
    up_commands = ["vagrant up --provision"]
    run_commands = [f'vagrant ssh default --command "cd /vagrant; {commands}"']

    returncode, output = _read(up_commands, cwd=cwd)
    if returncode != 0:
        raise RuntimeError("vagrant up failed with output: %s", output)

    returncode, output = _read(run_commands, cwd=cwd)
    return output


def test_help():
    """Test the help command"""
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    cwd = project_root.joinpath("example_repos/docker_module")

    result = vagrant(commands="poetry run pmt --help", cwd=cwd.absolute())
    assert b"Usage: pmt" in result


def test_py_doc_string_formatter():
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    cwd = project_root.joinpath("example_repos/docker_module")

    result = vagrant(commands="poetry run pmt lint --check -s py_doc_string_formatter", cwd=cwd.absolute())
    assert b"Lint result: py_doc_string_formatter 0" in result
