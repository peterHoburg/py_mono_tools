import subprocess


def kill_all_containers():
    result = subprocess.run(["docker-compose", "down", "--remove-orphans"])
