import pathlib
import subprocess

from py_mono_tools.config import consts, logger
from py_mono_tools.goals.interface import Deployers, Language


class PoetryBuilder(Deployers):
    """Class to interact with terraform."""

    name: str = "terraform"
    language = Language.PYTHON

    def _run_poetry(self, commands: list):
        logger.info("running command: %s", commands)

        cwd = consts.EXECUTED_FROM
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
        return self.run(dry_run=True)

    def build(self):
        commands = [
            "poetry",
            "build",
        ]
        return self._run_poetry(commands)

    def run(self, dry_run: bool = False):
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
