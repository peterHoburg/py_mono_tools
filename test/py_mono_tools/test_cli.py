import py_mono_tools
import pathlib
import subprocess  # nosec B404


def vagrant(cwd: str = None):
    up_commands = [
        "vagrant",
        "up",
        "--provision",
    ]
    run_commands = [
        "vagrant",
        "ssh",
        "default",
        "-c",
        '"cd /vagrant; poetry run pmt lint --check"',
    ]

    with subprocess.Popen(  # nosec B603
        run_commands,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        stdout_data, stderr_data = process.communicate()
    print(stdout_data)
    return stderr_data + stdout_data


def test_help():
    """Test help."""
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    cwd = project_root.joinpath("example_repos/docker_module")
    result = vagrant(cwd=cwd.absolute())
    assert result == 0
