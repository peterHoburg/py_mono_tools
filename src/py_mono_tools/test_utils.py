import subprocess  # nosec B404


"""Vagrant up; vagrant ssh -c "cd /vagrant; poetry run pmt lint --check"."""


def vagrant(cwd: str = None):
    commands = [
        "vagrant",
        "up",
        "--provision;",
        "vagrant",
        "ssh",
        "-c",
        '"cd /vagrant; poetry run pmt lint --check"',
    ]
    with subprocess.Popen(  # nosec B603
        commands,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        stdout_data, stderr_data = process.communicate()
