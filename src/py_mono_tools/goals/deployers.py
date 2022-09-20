"""Contains all deployers implementations."""
import pathlib
import subprocess  # nosec B404

from py_mono_tools.config import consts, logger
from py_mono_tools.goals.interface import Deployers, Language


class PoetryBuilder(Deployers):
    """Class to interact with poetry."""

    name: str = "poetry"
    language = Language.PYTHON

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
