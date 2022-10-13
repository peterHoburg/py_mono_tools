import pathlib
from py_mono_tools.test_utils import vagrant

# TODO halt vagrant post tests, start pre tests.


def test_help():
    """Test the help command"""
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    cwd = project_root.joinpath("example_repos/docker_module")

    returncode, result = vagrant(commands="poetry run pmt --help", cwd=cwd.absolute())
    assert b"Usage: pmt" in result


def test_py_doc_string_formatter():
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "test":
        project_root = project_root.parent
    project_root = project_root.parent
    cwd = project_root.joinpath("example_repos/docker_module")

    returncode, result = vagrant(commands="poetry run pmt lint --check -s py_doc_string_formatter", cwd=cwd.absolute())
    assert b"Lint result: py_doc_string_formatter 0" in result
