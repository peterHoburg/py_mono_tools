import os
import subprocess  # nosec B404
import sys

from py_mono_build.interfaces.base_class import BuildSystem


class Docker(BuildSystem):
    name: str = "docker"

    def build(self, force_rebuild: bool = False):
        uid = os.getuid()

        self.shutdown()
        self._build(uid, "amirainvest_com")

    def purge(self):
        raise NotImplementedError

    def run(self, command: str):
        self.build()

    def interactive(self):
        raise NotImplementedError

    def shutdown(self):
        self._kill_all_containers()

    def _build(self, uid: int, target: str):
        subprocess.check_output(  # nosec B603
            f"DOCKER_BUILDKIT=1 "
            f"BUILDKIT_PROGRESS=plain "
            f"docker-compose build "
            f"--build-arg USER_UID={uid} "
            f"--progress plain "
            f"{target}",
            # shell=True,
            cwd=self._root_path,
        )

    def _kill_all_containers(self):
        try:
            subprocess.check_output(  # nosec B607 B603
                "docker ps -q | xargs -r docker kill",
                # shell=True,
                cwd=self._root_path,
            )
            subprocess.check_output(  # nosec B607 B603
                ["docker-compose", "down", "--remove-orphans"],
                cwd=self._root_path,
            )
        except subprocess.CalledProcessError:
            sys.exit(1)
