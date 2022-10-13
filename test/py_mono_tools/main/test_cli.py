import pathlib

import pytest

from py_mono_tools.test_utils import vagrant_ssh
import typing as t


@pytest.mark.parametrize("vagrant", ["docker_module"], indirect=["vagrant"])
@pytest.mark.parametrize("conf_name", ["", "-n example_docker_module"])
class TestCli:
    def test_help(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(command=f"poetry run pmt {conf_name} --help", cwd=cwd.absolute())
        assert b"Usage: pmt" in result

    def test_isort(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint --check -s isort",
            cwd=cwd.absolute(),
        )
        assert b"main.py Imports are incorrectly sorted and/or formatted" in result

    def test_mypy(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s mypy",
            cwd=cwd.absolute(),
        )
        assert b"main.py:6: \x1b[1m\x1b[31merror:\x1b(B\x1b[m Missing return statement" in result

    def test_py_doc_string_formatter(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint --check -s py_doc_string_formatter",
            cwd=cwd.absolute(),
        )
        assert b"Lint result: py_doc_string_formatter 0" in result
