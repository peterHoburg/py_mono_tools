"""The Docker backend takes the goals instructions and runs them in a docker container."""
import os
import subprocess  # nosec B404
import sys
import typing as t
from pathlib import PosixPath

from py_mono_tools.backends.interface import Backend
from py_mono_tools.config import consts, logger


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

    def run(self, args: t.List[str], workdir: str = "/opt") -> t.Tuple[int, str]:
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
        with subprocess.Popen(  # nosec B603
            commands,
            cwd=consts.EXECUTED_FROM,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:

            stdout_data, stderr_data = process.communicate()
        return process.returncode, stderr_data.decode("utf-8") + stdout_data.decode("utf-8")

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

    def _build(self, uid: int):
        env = {
            "DOCKER_BUILDKIT": "1",
            "BUILDKIT_PROGRESS": "plain",
        }
        with subprocess.Popen(  # nosec B607 B603
            [
                "docker",
                "build",
                "--build-arg",
                f"USER_UID={uid}",
                "-t",
                "pmt_docker_backend",
                ".",
            ],
            env=env,
            cwd=consts.EXECUTED_FROM,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            stdout_data, stderr_data = process.communicate()

        logger.debug("Docker build stdout: \n%s", stdout_data.decode("utf-8"))
        logger.debug("Docker build stderr: \n%s", stderr_data.decode("utf-8"))
        if process.returncode != 0:
            logger.error(
                "Docker build failed: %s, stdout: %s stderr: %s",
                process.returncode,
                stdout_data.decode("utf-8"),
                stderr_data.decode("utf-8"),
            )
            sys.exit(1)

    def _kill_all_containers(self):
        try:
            subprocess.check_output(  # nosec B607 B603 B602
                "docker ps -q | xargs -r docker kill",
                shell=True,
                cwd=consts.EXECUTED_FROM,
            )
            # subprocess.check_output(  # nosec B607 B603
            #     ["docker-compose", "down", "--remove-orphans"],
            #     cwd=self._root_path,
            # )
        except subprocess.CalledProcessError:
            sys.exit(1)
