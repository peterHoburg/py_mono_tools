import importlib
import importlib.machinery
import importlib.util
import logging
import os
import pathlib
import pty
import subprocess  # nosec B404
import typing as t
from types import ModuleType

from py_mono_tools.config import consts, logger


def run_command_in_tty(
    command: t.Union[t.List[str], str],
    cwd: pathlib.Path,
    env: t.Optional[t.Dict[str, t.Any]] = None,
) -> t.Tuple[int, bytes]:
    if isinstance(command, list):
        command = " ".join(command)

    subprocess_kwargs = {}
    if env is not None:
        subprocess_kwargs["env"] = env

    command_fd, worker_fd = pty.openpty()

    p = subprocess.Popen(
        [command],
        preexec_fn=os.setsid,
        stdin=worker_fd,
        stdout=worker_fd,
        stderr=worker_fd,
        universal_newlines=True,
        shell=True,
        cwd=cwd,
        **subprocess_kwargs,
    )
    returncode = p.wait()
    os.close(worker_fd)

    output = []
    while True:
        try:
            data = os.read(command_fd, 1024)
        except OSError:
            break
        if not data:
            break
        output.append(data)
    output = b"".join(output)
    return returncode, output


def vagrant_ssh(command: str, cwd: pathlib.Path) -> t.Tuple[int, bytes]:
    run_commands = f'vagrant ssh default --command "cd /example_repos/docker_module; {command}"'
    returncode, output = run_command_in_tty(run_commands, cwd=cwd)
    return returncode, output


def example_repo_path(repo: str) -> pathlib.Path:
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "src":
        project_root = project_root.parent
    project_root = project_root.parent
    example_repo = project_root.joinpath("example_repos")
    cwd = example_repo.joinpath(repo)

    return cwd


def load_conf(conf_path: str) -> ModuleType:
    conf_location = f"{conf_path}/CONF"
    logger.debug("CONF location: %s", conf_location)

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    loader.exec_module(mod)

    return mod


def init_logger(verbose: bool, silent: bool = False):
    logging_level = logging.INFO
    if verbose:
        logging_level = logging.DEBUG
    if silent:
        logging_level = logging.ERROR

    logger.setLevel(logging_level)
    for handler in logger.handlers:
        handler.setLevel(logging_level)


def set_absolute_path(absolute_path: str):
    logger.info("Overwriting execution root path: %s", absolute_path)

    consts.EXECUTED_FROM = pathlib.Path(absolute_path).resolve()

    os.chdir(consts.EXECUTED_FROM.resolve())


def set_relative_path(relative_path: str):
    logger.info("Overwriting execution root path: %s", relative_path)

    consts.EXECUTED_FROM = consts.EXECUTED_FROM.joinpath(pathlib.Path(relative_path).resolve())
    os.chdir(consts.EXECUTED_FROM)


def set_path_from_conf_name(name: str):
    logger.info("Setting path from conf name: %s", name)

    for rel_path, _, filenames in os.walk("."):
        for filename in filenames:
            if filename == "CONF":
                path = pathlib.Path(rel_path).resolve()
                mod = load_conf(str(path))
                logger.debug("Found CONF: %s in %s", mod.NAME, path)
                if mod.NAME.strip().lower() == name.strip().lower():
                    logger.debug("Using CONF: %s in %s", mod.NAME, path)
                    set_absolute_path(str(path))
                    return