"""Contains all the implemented linters."""
import typing as t

from py_mono_tools.config import consts, GREEN, logger, RED, RESET
from py_mono_tools.goals.interface import Language, Linter


CHECK_STRING = " check"
MAX_LINE_LENGTH = 120


def _run(linter: str, args: t.List[str]) -> t.Tuple[str, int]:
    log_format = "\n" + "#" * 20 + "  {}  " + "#" * 20 + "\n"
    logs = ""

    logger.debug("Running %s: %s", linter, args)
    if len(args) > 0 and "docker" == args[0] and consts.CURRENT_BACKEND.name == "docker":  # type: ignore
        logger.debug("Bypassing docker backend for system backend. Linter: %s", linter)
        return_code, returned_logs = consts.BACKENDS["system"]().run(args)  # type: ignore
    else:
        return_code, returned_logs = consts.CURRENT_BACKEND.run(args)  # type: ignore
    logger.debug("%s return code: %s", linter, return_code)

    color = GREEN if return_code == 0 else RED
    logs += color
    logs += log_format.format(linter + " start")
    logs = logs + returned_logs
    logs += color
    logs += log_format.format(linter + " end")
    logs += RESET

    return logs, return_code


def _pull_latest_docker(image_name: str):
    logger.info("Pulling latest docker image: %s", image_name)
    consts.BACKENDS["system"]().run(["docker", "pull", image_name])  # type: ignore


class Bandit(Linter):
    """
    Bandit linter.

    Helps find common python security issues
    https://bandit.readthedocs.io/en/latest/
    """

    name: str = "bandit"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the bandit linter recursively."""
        args = [
            "bandit",
            "-r",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the bandit linter recursively."""
        return self.run()


class Black(Linter):
    """
    Black linter.

    Formats your code the correct way.
    https://black.readthedocs.io/en/stable/
    """

    name: str = "black"
    parallel_run: bool = False
    weight: int = 99
    language = Language.PYTHON

    def run(self):
        """
        Will run the black linter.

        NOTE: This WILL modify your files.
        """
        args = [
            "black",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name, args)

    def check(self):
        """
        Will run the black linter in check mode.

        NOTE: This will NOT modify your files.
        """
        args = [
            "black",
            "--check",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name + CHECK_STRING, args)


class Flake8(Linter):
    """
    Flake8 linter.

    Style checker for Python code.

    Flake8 runs: pycodestyle, pyflakes, and mccabe
    https://flake8.pycqa.org/en/latest/faq.html#why-does-flake8-use-ranges-for-its-dependencies

    WARNING: Flake8 must be run with the SAME version of python that your code will run on!

    The default max complexity is 10.
    The default max line length is 120.
    """

    name: str = "flake8"
    parallel_run: bool = False
    language = Language.PYTHON

    def __init__(self, args: t.Optional[t.List[str]] = None):
        """Will set the max complexity and max line length."""
        no_max_comp = True
        no_max_line = True
        if args is None:
            args = []

        for arg in args:
            if "--max-complexity" in arg:
                no_max_comp = False
            if "--max-line-length" in arg:
                no_max_line = False

        if no_max_comp is True:
            args.append("--max-complexity=10")
        if no_max_line is True:
            args.append(f"--max-line-length={MAX_LINE_LENGTH}")

        super().__init__(args)

    def run(self):
        """Will run the flake8 linter."""
        args = [
            "flake8",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name, args)

    def check(self):
        """Will run the flake8 linter."""
        return self.run()


class ISort(Linter):
    """
    ISort linter.

    Sorts python imports.

    https://pycqa.github.io/isort/

    NOTE: Isort run WILL modify your files.
    """

    name: str = "isort"
    parallel_run: bool = False
    weight = 100
    language = Language.PYTHON

    def run(self):
        """
        Will run the isort linter.

        NOTE: This WILL modify your files.
        """
        args = [
            "isort",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """
        Will run the isort linter in check mode.

        Note: This will NOT modify your files.
        """
        args = [
            "isort",
            "-c",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name + CHECK_STRING, args)


class Mccabe(Linter):
    """
    Flake8 runs Mccabe.

    Only use this if you do not also run Flake8
    """

    name: str = "mccabe"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the mccabe linter."""
        args = [
            "python",
            "-m",
            "mccabe",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the mccabe linter."""
        self.run()


class Mypy(Linter):
    """
    Mypy linter.

    Python static type checker.
    https://mypy.readthedocs.io/en/stable/index.html
    """

    name: str = "mypy"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the mypy linter."""
        args = [
            "mypy",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the mypy linter."""
        return self.run()


class PyDocStringFormatter(Linter):
    """
    PyDocStringFormatter linter.

    A tool to automatically format Python docstrings to follow recommendations from PEP 8 and PEP 257.
    https://pydocstringformatter.readthedocs.io/en/latest/index.html
    """

    name: str = "py_doc_string_formatter"
    parallel_run: bool = False
    weight = 98
    language = Language.PYTHON

    def run(self):
        """
        Will run the pydocstringformatter linter.

        NOTE: This WILL modify your files.
        """
        args = [
            "pydocstringformatter",
            "-w",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name, args)

    def check(self):
        """
        Will run the pydocstringformatter linter in check mode.

        NOTE: This will NOT modify your files.
        """
        args = [
            "pydocstringformatter",
            consts.EXECUTED_FROM,
            *self._args,
        ]

        return _run(self.name + CHECK_STRING, args)


class Pydocstyle(Linter):
    """
    Pydocstyle linter.

    Static analysis of docstrings to follow PEP 257.
    https://www.pydocstyle.org/en/stable/
    """

    name: str = "pydocstyle"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the pydocstyle linter."""
        args = [
            "pydocstyle",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the pydocstyle linter."""
        return self.run()


class Pyflakes(Linter):
    """
    Flake8 runs pyflakes.

    Only use this if you do not also run Flake8
    """

    name: str = "pyflakes"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the pyflakes linter."""
        args = [
            "pyflakes",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the pyflakes linter."""
        return self.run()


class Pylint(Linter):
    """
    Pylint linter.

    Static code analysis for Python. Checks for errors, code smells, and formatting.
    https://pylint.pycqa.org/en/latest/
    """

    name: str = "pylint"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the pylint linter."""
        args = [
            "pylint",
            consts.EXECUTED_FROM,
            *self._args,
        ]
        return _run(self.name, args)

    def check(self):
        """Will run the pylint linter."""
        return self.run()


class PipAudit(Linter):
    """
    PipAudit linter.

    A tool to check for vulnerable Python packages.
    https://pypi.org/project/pip-audit/
    """

    name: str = "pip-audit"
    parallel_run: bool = True
    language = Language.PYTHON

    def run(self):
        """Will run the pip-audit linter."""
        base_args = [
            "pip-audit",
            "-S",
            "-s",
        ]
        args = [*base_args, "osv", *self._args]
        logs, return_code = _run(self.name, args)

        if return_code == 0:
            args = [*base_args, "pypi", *self._args]
            logs_pypi, return_code = _run(self.name, args)
            logs += logs_pypi

        return logs, return_code

    def check(self):
        """Will run the pip-audit linter."""
        return self.run()


class CheckOV(Linter):
    """
    CheckOV linter.

    Cloud infrastructure configurations to find misconfigurations.
    https://www.checkov.io/1.Welcome/Quick%20Start.html

    NOTE: This will ALWAYS run in a docker container. CheckOV will not be installed on the system.
    """

    name: str = "checkov"
    parallel_run: bool = True
    language = Language.TERRAFORM

    def run(self):
        """Will run the checkov linter in a docker container."""
        image_name = "bridgecrew/checkov"
        args = [
            "docker",
            "run",
            "--tty",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/tf",
            "--workdir",
            "/tf",
            image_name,
            "--directory",
            "/tf",
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the checkov linter in a docker container."""
        return self.run()


class TerrascanTerraform(Linter):
    """
    Terrascan linter.

    Only running on Terraform files

    Detect compliance and security violations across Infrastructure as Code
    https://runterrascan.io/docs/

    NOTE: This will ALWAYS run in a docker container. Terrascan will not be installed on the system.
    """

    name: str = "terrascan_terraform"
    parallel_run: bool = True
    language = Language.TERRAFORM

    def run(self):
        """Will run the terrascan linter for terraform in a docker container."""
        image_name = "tenable/terrascan"
        args = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/iac",
            "--workdir",
            "/iac",
            image_name,
            "scan",
            "-i",
            "terraform",
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the terrascan linter for terraform in a docker container."""
        return self.run()


class TFLint(Linter):
    """
    TFLint linter.

    Find possible errors (like illegal instance types) for Major Cloud providers
    https://github.com/terraform-linters/tflint

    WARNING: TFLint always checks only the current root module (no recursive check). This makes it a pain
    to work with.

    NOTE: This will ALWAYS run in a docker container. TFLint will not be installed on the system.
    """

    name: str = "tflint"
    parallel_run: bool = True
    language = Language.TERRAFORM

    def run(self):
        """Will run the tflint linter in a docker container."""
        image_name = "ghcr.io/terraform-linters/tflint"
        args = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{consts.EXECUTED_FROM}:/data",
            "-t",
            image_name,
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the tflint linter in a docker container."""
        return self.run()


class TFSec(Linter):
    """
    TFSec linter.

    Static analysis security scanner for Terraform
    https://aquasecurity.github.io/tfsec/v1.27.6/

    NOTE: This will ALWAYS run in a docker container. TFsec will not be installed on the system.
    """

    name: str = "tfsec"
    parallel_run: bool = True
    language = Language.TERRAFORM

    def run(self):
        """Will run the tfsec linter in a docker container."""
        image_name = "aquasec/tfsec"
        args = [
            "docker",
            "run",
            "--rm",
            "-it",
            "-v",
            f"{consts.EXECUTED_FROM}:/src",
            image_name,
            "/src",
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the tfsec linter in a docker container."""
        return self.run()


class TerraformFmt(Linter):
    """
    Terraform fmt linter.

    https://www.terraform.io/cli/commands/fmt

    NOTE: This will ALWAYS run in a docker container. Terraform will not be installed on the system.
    """

    name: str = "terraform_fmt"
    parallel_run: bool = False
    weight = 100
    language = Language.TERRAFORM

    def run(self):
        """Will run the terraform fmt linter in a docker container."""
        image_name = "hashicorp/terraform"
        args = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/opt",
            "--workdir",
            "/opt",
            image_name,
            "fmt",
            "-recursive",
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the terraform fmt check linter in a docker container."""
        self._args = ["-check"] + self._args
        return self.run()


class TerrascanDocker(Linter):
    """
    Terrascan linter.

    Only for Dockerfiles.

    Detect compliance and security violations across Infrastructure as Code
    https://runterrascan.io/docs/

    NOTE: This will ALWAYS run in a docker container. Terrascan will not be installed on the system.
    """

    name: str = "terrascan_docker"
    parallel_run: bool = True
    language = Language.TERRAFORM

    def run(self):
        """Will run the terrascan linter for dockerfiles in a docker container."""
        image_name = "tenable/terrascan"
        args = [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{consts.EXECUTED_FROM}:/iac",
            "--workdir",
            "/iac",
            image_name,
            "scan",
            "-i",
            "docker",
            *self._args,
        ]
        _pull_latest_docker(image_name)
        return _run(self.name, args)

    def check(self):
        """Will run the terrascan linter for dockerfiles in a docker container."""
        return self.run()


DEFAULT_PYTHON = [
    ISort(),
    Black(args=[f"--line-length={MAX_LINE_LENGTH}"]),
    PyDocStringFormatter(),
    Bandit(),
    Flake8(args=["--ignore=E203", "--ignore=W503"]),
    Mypy(),
    Pydocstyle(),
    Pylint(args=[f"--max-line-length={MAX_LINE_LENGTH}"]),
    # PipAudit(),
]

DEFAULT_TERRAFORM = [
    TerraformFmt(),
    CheckOV(),
    TerrascanTerraform(args=["-d", "./terraform"]),
    TFSec(),
]

DEFAULT_DOCKER = [
    TerrascanDocker(),
]
