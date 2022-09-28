"""Contains all deployers implementations."""
import json
import os
import pathlib
import subprocess  # nosec B404
import typing as t

from py_mono_tools.config import consts, logger
from py_mono_tools.goals.interface import Deployer, Language


class PoetryDeployer(Deployer):
    """Class to interact with poetry."""

    name: str = "poetry"
    language = Language.PYTHON

    def __init__(self, args: t.Optional[t.List[str]] = None, pyproject_loc: t.Optional[str] = None):
        """Will initialize the poetry deployer."""
        super().__init__(args)
        self._pyproject_loc = pyproject_loc

    def _run_poetry(self, commands: list):
        logger.info("running command: %s", commands)

        cwd = consts.EXECUTED_FROM
        if self._pyproject_loc is None:
            logger.error("pyproject.toml location not set")
            raise ValueError("pyproject.toml location not set")
        cwd = cwd / pathlib.Path(self._pyproject_loc).parent
        cwd = cwd.resolve()
        logger.info("cwd: %s", cwd)

        with subprocess.Popen(  # nosec B603
            commands,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            stdout_data, stderr_data = process.communicate()

        return process.returncode, stderr_data.decode("utf-8") + stdout_data.decode("utf-8")

    def plan(self):
        """Win run poetry build and poetry publish --dry-run."""
        return self.run(dry_run=True)

    def build(self):
        """Will run poetry build."""
        commands = [
            "poetry",
            "build",
        ]
        return self._run_poetry(commands)

    def run(self, dry_run: bool = False):
        """Will run poetry publish."""
        return_code, build_logs = self.build()

        logger.debug("build_return_code: %s build logs: %s", return_code, build_logs)

        if return_code != 0:
            logger.error("build failed: %s", build_logs)
            return return_code, build_logs

        commands = [
            "poetry",
            "publish",
        ]
        if dry_run is True:
            commands.append("--dry-run")

        return_code, run_logs = self._run_poetry(commands)
        logger.debug("run_return_code: %s run logs: %s", return_code, run_logs)

        return return_code, build_logs + run_logs


class TerraformDeployer(Deployer):
    """Class that uses the terraform CLI (inside a docker container) to deploy the infrastructure."""

    name: str = "terraform"
    language = Language.TERRAFORM

    def __init__(
        self,
        args: t.Optional[t.List[str]] = None,
        terraform_version: t.Optional[str] = "1.3.0",
        terraform_dir: t.Optional[str] = None,
    ):
        """Will initialize the terraform deployer."""
        super().__init__(args)
        self._terraform_version = terraform_version
        self._terraform_dir = terraform_dir

    @staticmethod
    def _get_env():
        token = os.environ.get("TF_TOKEN", None)

        if token is None:
            try:
                with open(f"{pathlib.Path.home()}/.terraform.d/credentials.tfrc.json", "r", encoding="UTF-8") as file:
                    cred_file = json.load(file)
                    token = cred_file["credentials"]["app.terraform.io"]["token"]
            except (FileNotFoundError, json.decoder.JSONDecodeError, KeyError):
                logger.exception("failed to get token from credentials.tfrc.json")

        env = {
            "TF_TOKEN_app_terraform_io": token,
            "TF_IN_AUTOMATION": "true",
            # "TF_WORKSPACE"
        }

        return env

    def _run(self, build_or_plan: str):
        commands = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{consts.EXECUTED_FROM}:/opt",
            "-w",
            "/opt",
        ]
        env = self._get_env()
        for key, value in env.items():
            commands.extend(["-e", f"{key}={value}"])

        commands.append(
            f"hashicorp/terraform:{self._terraform_version}",
        )
        if self._terraform_dir is not None:
            commands.append(f"-chdir={self._terraform_dir}")

        commands.append(build_or_plan)

        if "-auto-approve" in self._args and build_or_plan == "plan":
            logger.warning("auto approve is set, but this is a plan, ignoring")
            self._args.remove("-auto-approve")

        commands.extend(self._args)

        logger.info("running command: %s", commands)

        with subprocess.Popen(  # nosec B603
            commands,
            cwd=consts.EXECUTED_FROM,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        ) as process:
            stdout_data, stderr_data = process.communicate()

        return process.returncode, stderr_data.decode("utf-8") + stdout_data.decode("utf-8")

    def plan(self):
        """Will run terraform plan."""
        return self._run("plan")

    def build(self):
        """Will run terraform plan."""
        return self.plan()

    def run(self):
        """Will run terraform apply."""
        return self._run("apply")
