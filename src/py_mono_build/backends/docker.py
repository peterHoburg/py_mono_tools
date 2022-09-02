import os
import subprocess  # nosec B404
import sys
import typing as t

from py_mono_build.backends.interface import Backend
from py_mono_build.config import logger


class Docker(Backend):
    name: str = "docker"

    def build(self, force_rebuild: bool = False):
        uid = os.getuid()

        self.shutdown()
        self._build(uid)

    def purge(self):
        raise NotImplementedError

    def run(self, args: t.List[str]):
        commands = [
            "docker",
            "run",
            "-it",
            "pmb_docker_backend",
        ]
        for arg in args:
            if type(arg) != str:
                commands.append("/opt/")
            else:
                commands.append(arg)

        logger.info("running command: %s", commands)

        self.build()
        process = subprocess.Popen(  # nosec B603
            commands,
            cwd=self._root_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout_data, stderr_data = process.communicate()
        return process.returncode, stderr_data.decode("utf-8") + stdout_data.decode(
            "utf-8"
        )

    def interactive(self):
        raise NotImplementedError

    def shutdown(self):
        self._kill_all_containers()

    def _build(self, uid: int):
        env = {
            "DOCKER_BUILDKIT": "1",
            "BUILDKIT_PROGRESS": "plain",
        }
        process = subprocess.Popen(  # nosec B603
            [
                "docker",
                "build",
                "--build-arg",
                f"USER_UID={uid}",
                "-t",
                "pmb_docker_backend",
                ".",
            ],
            env=env,
            cwd=self._root_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
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
            subprocess.check_output(  # nosec B607 B603
                "docker ps -q | xargs -r docker kill",
                shell=True,
                cwd=self._root_path,
            )
            # subprocess.check_output(  # nosec B607 B603
            #     ["docker-compose", "down", "--remove-orphans"],
            #     cwd=self._root_path,
            # )
        except subprocess.CalledProcessError:
            sys.exit(1)
