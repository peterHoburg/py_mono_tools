import json
import pathlib

import pytest

from py_mono_tools.utils import vagrant_ssh
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

    def test_isort_machine_output(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} -mo lint --check -s isort",
            cwd=cwd.absolute(),
        )

        json_result = json.loads(result)
        assert json_result["returncode"] == 1

        isort_result = json_result["goals"]["isort"]

        assert isort_result["name"] == "isort"
        assert isort_result["returncode"] == 1
        assert "main.py Imports are incorrectly sorted and/or formatted" in isort_result["output"]

    def test_black(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint --check -s black",
            cwd=cwd.absolute(),
        )
        assert b"Lint result: black 0 " in result

    def test_black_machine_output(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} -mo lint --check -s black",
            cwd=cwd.absolute(),
        )
        json_result = json.loads(result)
        assert json_result["returncode"] == 0

        black_result = json_result["goals"]["black"]

        assert black_result["name"] == "black"
        assert black_result["returncode"] == 0

    def test_py_doc_string_formatter(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint --check -s py_doc_string_formatter",
            cwd=cwd.absolute(),
        )
        assert b"Lint result: py_doc_string_formatter 0" in result

    def test_bandit(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s bandit",
            cwd=cwd.absolute(),
        )
        assert b"Lint result: bandit 0" in result

    def test_flake8(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s flake8",
            cwd=cwd.absolute(),
        )
        assert b"F401" in result

    def test_mypy(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s mypy",
            cwd=cwd.absolute(),
        )
        assert b"Missing return statement" in result

    def test_pydocstyle(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s pydocstyle",
            cwd=cwd.absolute(),
        )
        assert b"__init__.py:1 at module level:" in result

    def test_pylint(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s pylint",
            cwd=cwd.absolute(),
        )
        assert b"rc/docker_module/main.py:1:0: C0114: Missing module docstring (missing-module-docstring)" in result

    @pytest.mark.skip()
    def test_pip_audit(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} lint -s pip-audit",
            cwd=cwd.absolute(),
        )
        assert b"Lint result: pip-audit 0" in result

    def test_terrascan_docker_mo(self, vagrant: pathlib.Path, conf_name: t.Optional[str]):
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} -mo lint -s terrascan_docker",
            cwd=cwd.absolute(),
        )
        json_result = json.loads(result)
        assert json_result["returncode"] == 1

        terrascan = json_result["goals"]["terrascan_docker"]

        assert terrascan["name"] == "terrascan_docker"
        assert terrascan["returncode"] == 3

        output = json.loads(terrascan["output"])
        for violation in output["results"]["violations"]:
            assert violation["file"] == "Dockerfile"

    def test_all(self, vagrant: pathlib.Path, conf_name: t.Optional[str]) -> None:
        cwd = vagrant
        returncode, result = vagrant_ssh(
            command=f"poetry run pmt {conf_name} -mo lint --check",
            cwd=cwd.absolute(),
        )

        json_result = json.loads(result)
        assert json_result["returncode"] == 1
