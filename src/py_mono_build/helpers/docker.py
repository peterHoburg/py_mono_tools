import subprocess

from py_mono_build.interfaces.base_class import BuildSystem


class Docker(BuildSystem):
    name = "docker"

    def build(self, force_rebuild: bool = False):
        self.shutdown()

    def purge(self):
        pass

    def run(self, command: str):
        pass

    def shutdown(self):
        self._kill_all_containers()

    @staticmethod
    def _kill_all_containers():
        result = subprocess.run(["docker-compose", "down", "--remove-orphans"])
        if result.returncode != 0:
            exit(1)
        result = subprocess.run(["docker", "ps", "-q", "|", "xargs", "-r", "docker", "kill"])
        if result.returncode != 0:
            exit(1)
