from py_mono_tools.test_utils import vagrant, example_repo_path

# TODO halt vagrant post tests, start pre tests.


def test_help():
    """Test the help command"""
    cwd = example_repo_path("docker_module")
    returncode, result = vagrant(commands="poetry run pmt --help", cwd=cwd.absolute())
    assert b"Usage: pmt" in result


def test_isort():
    cwd = example_repo_path("docker_module")
    returncode, result = vagrant(commands="poetry run pmt lint --check -s isort", cwd=cwd.absolute())
    assert b"main.py Imports are incorrectly sorted and/or formatted" in result


def test_mypy():
    cwd = example_repo_path("docker_module")
    returncode, result = vagrant(commands="poetry run pmt lint --check -s mypy", cwd=cwd.absolute())
    assert b"main.py:6: \x1b[1m\x1b[31merror:\x1b(B\x1b[m Missing return statement" in result


def test_py_doc_string_formatter():
    cwd = example_repo_path("docker_module")
    returncode, result = vagrant(commands="poetry run pmt lint --check -s py_doc_string_formatter", cwd=cwd.absolute())
    assert b"Lint result: py_doc_string_formatter 0" in result
