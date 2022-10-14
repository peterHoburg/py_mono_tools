"""The Docker backend takes the goals instructions and runs them in a docker container."""
import os
import sys
import typing as t
from pathlib import PosixPath

from py_mono_tools.backends.interface import Backend
from py_mono_tools.config import consts, logger
from py_mono_tools.utils import run_command_in_tty


# pylint: disable=R0801
class Docker(Backend):
    """Class to interact with a docker container."""

    name: str = "docker"

    def build(self, force_rebuild: bool = False):
        """Will shut down any running containers and builds a new one."""
        uid = os.getuid()

        self.shutdown()
        self._build(uid)

    def purge(self):
        """Will do nothing for the docker backend."""
        raise NotImplementedError

    def run(self, args: t.List[str], workdir: str = "/opt") -> t.Tuple[int, bytes]:
        """Will run a command in a docker container."""
        self.build()
        commands = [
            "docker",
            "run",
            "--rm",
            "-w",
            workdir,
            "-v",
            f"{consts.EXECUTED_FROM}:{workdir}",
            "-it",
            "pmt_docker_backend",
        ]
        for arg in args:
            if isinstance(arg, PosixPath):
                commands.append("/opt/")
            else:
                commands.append(arg)

        logger.info("running command: %s", commands)

        self.build()

        return run_command_in_tty(commands, consts.EXECUTED_FROM)

    def interactive(self, workdir: str = "/opt"):
        """Will drop user into interactive docker session."""
        self.build()
        commands = [
            "docker",
            "run",
            "--rm",
            "-w",
            workdir,
            "-v",
            f"{consts.EXECUTED_FROM}:{workdir}",
            "-it",
            "pmt_docker_backend",
            "/bin/bash",
        ]
        os.execvp(file=commands[0], args=commands)  # nosec B606

    def shutdown(self):
        """Will shut down any running containers."""
        self._kill_all_containers()

    @staticmethod
    def _build(uid: int):
        env = {
            "DOCKER_BUILDKIT": "1",
            "BUILDKIT_PROGRESS": "plain",
        }
        commands = [
            "docker",
            "build",
            "--build-arg",
            f"USER_UID={uid}",
            "-t",
            "pmt_docker_backend",
            ".",
        ]
        returncode, output = run_command_in_tty(commands, consts.EXECUTED_FROM, env)

        logger.debug("Docker build stderr: \n%s", output.decode("utf-8"))
        if returncode != 0:
            logger.error(
                "Docker build failed: %s, stdout: %s stderr: %s",
                returncode,
                output.decode("utf-8"),
                output.decode("utf-8"),
            )
            sys.exit(1)

    @staticmethod
    def _kill_all_containers():
        command = "docker ps -q | xargs -r docker kill"
        returncode, output = run_command_in_tty(command, consts.EXECUTED_FROM, env)
        if returncode != 0:
            sys.exit(1)
