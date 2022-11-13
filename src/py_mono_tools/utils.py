"""A utils file. This is a file that contains a bunch of functions that are used in multiple places."""
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
from py_mono_tools.cli_interface import GoalOutput
from py_mono_tools.config import cfg, GREEN, logger, RED, RESET
from py_mono_tools.goals import deployers as deployers_mod, linters as linters_mod, testers as testers_mod
from py_mono_tools.goals.interface import Deployer, Language, Linter, Tester


def run_command_in_tty(
    command: t.Union[t.List[str], str],
    cwd: pathlib.Path,
    env: t.Optional[t.Dict[str, t.Any]] = None,
) -> t.Tuple[int, bytes]:
    """
    Will run a command in a true TTY.

    Python makes this non-trivial.
    """
    if isinstance(command, list):
        command = " ".join(command)

    subprocess_kwargs = {}
    if env is not None:
        subprocess_kwargs["env"] = env

    command_fd, worker_fd = pty.openpty()

    # pylint: disable-next=W1509. R1732
    process = subprocess.Popen(  # nosec B602
        [command],  # type: ignore
        # This is doing something weird. Using shell, and a single string arg to pass the entire string to the shell.
        preexec_fn=os.setsid,
        stdin=worker_fd,
        stdout=worker_fd,
        stderr=worker_fd,
        universal_newlines=True,
        shell=True,
        cwd=cwd,
        **subprocess_kwargs,
    )
    returncode = process.wait()
    os.close(worker_fd)

    outputs = []
    while True:
        try:
            data = os.read(command_fd, 1024)
        except OSError:
            break
        if not data:
            break
        outputs.append(data)
    output = b"".join(outputs)
    return returncode, output


def vagrant_ssh(command: str, cwd: pathlib.Path) -> t.Tuple[int, bytes]:
    """Will run a command inside a vagrant box."""
    run_commands = f'vagrant ssh default --command "cd /example_repos/docker_module; {command}"'
    returncode, output = run_command_in_tty(run_commands, cwd=cwd)
    return returncode, output


def example_repo_path(repo: str) -> pathlib.Path:
    """Will return the path to the example repo."""
    path = pathlib.Path(__file__)
    project_root = path
    while project_root.name != "src":
        project_root = project_root.parent
    project_root = project_root.parent
    example_repo = project_root.joinpath("example_repos")
    cwd = example_repo.joinpath(repo)

    return cwd


def load_conf(conf_path: str) -> ModuleType:
    """
    Will load the CONF file at the given path.

    WARNING: This will execute any code that would normally run at import time!
    """
    conf_location = f"{conf_path}/CONF"
    logger.debug("CONF location: %s", conf_location)

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    loader.exec_module(mod)

    return mod


def init_logger(verbose: bool, silent: bool = False):
    """
    Will initialize the logger.

    The logging level depends on the verbose flag.
    """
    logging_level = logging.INFO
    if verbose:
        logging_level = logging.DEBUG
    if silent:
        logging_level = logging.ERROR

    logger.setLevel(logging_level)
    for handler in logger.handlers:
        handler.setLevel(logging_level)


def set_absolute_path(absolute_path: str):
    """Will set cfg.EXECUTED_FROM when the CLI is given an absolute path."""
    logger.info("Overwriting execution root path: %s", absolute_path)

    cfg.EXECUTED_FROM = pathlib.Path(absolute_path).resolve()

    os.chdir(cfg.EXECUTED_FROM.resolve())


def set_relative_path(relative_path: str):
    """Will set cfg.EXECUTED_FROM when the CLI is given a relative path."""
    logger.info("Overwriting execution root path: %s", relative_path)

    cfg.EXECUTED_FROM = cfg.EXECUTED_FROM.joinpath(pathlib.Path(relative_path).resolve())
    os.chdir(cfg.EXECUTED_FROM)


def set_path_from_conf_name(name: str):
    """
    Will set the path based on the CONF file name.

    This will search through all child directories until a CONF file is found that matches the given name. Once found,
    the absolute path is set from the location of the CONF file.
    """
    logger.info("Setting path from conf name: %s", name)

    # pylint: disable=R0801
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


def machine_goal_to_human_output(goal: GoalOutput) -> str:
    """Will convert the given GoalOutput into colored, human-readable logs."""
    header_footer_format = "\n" + "#" * 20 + "  {}  " + "#" * 20 + "\n"
    if goal.returncode == 0:
        color = GREEN
    else:
        color = RED
    log = (
        RESET
        + color
        + header_footer_format.format(goal.name + " START")
        + goal.output.decode("UTF-8")
        + header_footer_format.format(goal.name + " END")
        + RESET
    )
    return log


def find_goals():
    """Will find all goals that inherent from the goal ABC."""
    goals = [
        (linters_mod, Linter, "linters", cfg.ALL_LINTERS, cfg.ALL_LINTER_NAMES),
        (deployers_mod, Deployer, "deployers", cfg.ALL_DEPLOYERS, cfg.ALL_DEPLOYER_NAMES),
        (testers_mod, Tester, "testers", cfg.ALL_TESTERS, cfg.ALL_TESTER_NAMES),
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

    cfg.ALL_BACKENDS = [Docker, System]
    cfg.ALL_BACKEND_NAMES = [Docker.name, System.name]


def init_backend(_build_system: str):
    """Will run the init for the given backand and set it in cfg.CURRENT_BACKEND."""
    logger.debug("Initializing build system: %s", _build_system)

    cfg.BACKENDS = {
        Docker.name: Docker,
        System.name: System,
    }

    cfg.CURRENT_BACKEND = cfg.BACKENDS[_build_system]()


def filter_linters(specific_linters: t.List[str], language: t.Optional[Language]) -> t.List[Linter]:
    """
    Will filter down the list of linters based on if a specific language is requested, or if a single linter is.

    requested.
    """
    conf_linters: t.List[Linter] = cfg.CONF.LINT  # type: ignore
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
