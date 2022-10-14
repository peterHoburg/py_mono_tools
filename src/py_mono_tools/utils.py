import importlib
import importlib.machinery
import importlib.util
import inspect
import logging
import os
import pathlib
import pty
import subprocess  # nosec B404
import typing as t
from types import ModuleType

from py_mono_tools.backends import Docker, System
from py_mono_tools.config import consts, logger
from py_mono_tools.goals import deployers as deployers_mod, linters as linters_mod, testers as testers_mod
from py_mono_tools.goals.interface import Deployer, Language, Linter, Tester


def run_command_in_tty(command: str, cwd: pathlib.Path) -> t.Tuple[int, bytes]:
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
    run_commands = f'vagrant ssh default --command "cd /vagrant; {command}"'
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


def find_goals():
    goals = [
        (linters_mod, Linter, "linters", consts.ALL_LINTERS, consts.ALL_LINTER_NAMES),
        (deployers_mod, Deployer, "deployers", consts.ALL_DEPLOYERS, consts.ALL_DEPLOYER_NAMES),
        (testers_mod, Tester, "testers", consts.ALL_TESTERS, consts.ALL_TESTER_NAMES),
    ]

    for goal in goals:
        goal_mod, goal_abc, goal_name, consts_goal_instances, consts_goal_names = goal
        logger.debug("Finding %s", goal_name)
        goal_classes = inspect.getmembers(goal_mod, inspect.isclass)
        goal_instances = [
            goal_class[1]()
            for goal_class in goal_classes
            if issubclass(goal_class[1], goal_abc) and goal_class[1] != goal_abc
        ]
        consts_goal_instances.extend(goal_instances)

        for goal_instance in goal_instances:
            consts_goal_names.append(goal_instance.name)

    consts.ALL_BACKENDS = [Docker, System]
    consts.ALL_BACKEND_NAMES = [Docker.name, System.name]


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


def init_backend(_build_system: str):
    logger.debug("Initializing build system: %s", _build_system)

    consts.BACKENDS = {
        Docker.name: Docker,
        System.name: System,
    }

    consts.CURRENT_BACKEND = consts.BACKENDS[_build_system]()


def filter_linters(specific_linters: t.List[str], language: t.Optional[Language]) -> t.List[Linter]:
    conf_linters: t.List[Linter] = consts.CONF.LINT  # type: ignore
    logger.debug("Linters: %s", conf_linters)
    linters_to_run: t.List[Linter] = []
    specific_linters = [s.strip().lower() for s in specific_linters]

    if language is None and not specific_linters:
        logger.debug("No language or specific linters specified. Running all linters.")
        linters_to_run = conf_linters
    else:
        logger.debug("Language: %s, specific: %s", language, specific_linters)
        for linter in conf_linters:
            if linter.name.strip().lower() in specific_linters:
                linters_to_run.append(linter)
                continue
            if linter.language == language:
                linters_to_run.append(linter)

    logger.debug("Linters to run: %s", linters_to_run)
    return linters_to_run
