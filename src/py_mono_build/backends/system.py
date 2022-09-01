import subprocess  # nosec B404

from py_mono_build.backends.interface import Backend


class System(Backend):
    name: str = "system"

    def build(self, force_rebuild: bool = False):
        pass

    def purge(self):
        raise NotImplementedError

    def run(self, command: str):
        process = subprocess.Popen(  # nosec B603
            command,
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
        pass
