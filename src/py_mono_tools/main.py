"""Contains all the commands that the CLI can execute."""
import importlib
import importlib.machinery
import importlib.util
import inspect
import logging
import os
import os.path
import pathlib
import sys
import typing as t
from types import ModuleType

import click

from py_mono_tools.backends import Docker, System
from py_mono_tools.config import consts, logger
from py_mono_tools.goals import deployers as deployers_mod, linters as linters_mod, testers as testers_mod
from py_mono_tools.goals.interface import Deployer, Language, Linter, Tester


logger.info("Starting main")


def _find_goals():
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


_find_goals()


def _load_conf(conf_path: str) -> ModuleType:
    conf_location = f"{conf_path}/CONF"
    logger.debug("CONF location: %s", conf_location)

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    loader.exec_module(mod)

    return mod


def _init_logger(verbose: bool):
    if verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)


def _set_absolute_path(absolute_path: str):
    logger.info("Overwriting execution root path: %s", absolute_path)

    consts.EXECUTED_FROM = pathlib.Path(absolute_path).resolve()

    os.chdir(consts.EXECUTED_FROM.resolve())


def _set_relative_path(relative_path: str):
    logger.info("Overwriting execution root path: %s", relative_path)

    consts.EXECUTED_FROM = consts.EXECUTED_FROM.joinpath(pathlib.Path(relative_path).resolve())
    os.chdir(consts.EXECUTED_FROM)


def _set_path_from_conf_name(name: str):
    logger.info("Setting path from conf name: %s", name)

    for rel_path, _, filenames in os.walk("."):
        for filename in filenames:
            if filename == "CONF":
                path = pathlib.Path(rel_path).resolve()
                mod = _load_conf(str(path))
                logger.debug("Found CONF: %s in %s", mod.NAME, path)
                if mod.NAME.strip().lower() == name.strip().lower():
                    logger.debug("Using CONF: %s in %s", mod.NAME, path)
                    _set_absolute_path(str(path))
                    return


def _init_backend(_build_system: str):
    logger.debug("Initializing build system: %s", _build_system)

    consts.BACKENDS = {
        Docker.name: Docker,
        System.name: System,
    }

    consts.CURRENT_BACKEND = consts.BACKENDS[_build_system]()


def _filter_linters(specific_linters: t.List[str], language: t.Optional[Language]) -> t.List[Linter]:
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


@click.group()
@click.option(
    "--backend",
    default=None,
    type=str,
    help="""
Default backend is \"system\".
This can be set via this flag, the BACKEND var in CONF, or defaulted to system.
""",
)
@click.option("--absolute_path", "-ap", default=None, type=click.Path())
@click.option("--relative_path", "-rp", default=None, type=click.Path())
@click.option("--name", "-n", default=None, type=str, help="Name as defined in CONF NAME=...")
@click.option("--verbose", "-v", default=False, is_flag=True)
def cli(backend, absolute_path, relative_path, name, verbose):
    """Py mono tool is a CLI tool that simplifies using python in a monorepo."""
    logger.info("Starting cli")

    if "--help" in sys.argv or "-h" in sys.argv:
        return

    _init_logger(verbose=verbose)

    logger.debug("Executed from: %s", consts.EXECUTED_FROM)
    logger.debug("Current backend: %s", consts.CURRENT_BACKEND)
    logger.debug("Backends: %s", consts.BACKENDS)

    if absolute_path is not None:
        _set_absolute_path(absolute_path=absolute_path)
    elif relative_path is not None:
        _set_relative_path(relative_path=relative_path)
    elif name is not None:
        _set_path_from_conf_name(name)

    try:
        mod = _load_conf(consts.EXECUTED_FROM)
        consts.CONF = mod
        if backend is None:
            try:
                backend = consts.CONF.BACKEND
            except AttributeError:
                backend = "system"

        logger.info("Using backed: %s", backend)

        _init_backend(backend)
    except FileNotFoundError:
        logger.error("No CONF file found in %s", consts.EXECUTED_FROM)


@cli.command()
@click.option("--check", is_flag=True, default=False)
@click.option(
    "--specific",
    "-s",
    multiple=True,
    default=[],
    help=f"""
    Specify one or more linters to run. NOTE: The linter MUST be listed in the respected CONF file.

    All Linters:
    {consts.ALL_LINTER_NAMES}
    """,
    shell_complete=consts.ALL_LINTER_NAMES,
)
@click.option("--fail_fast", "-ff", is_flag=True, default=False, help="Stop on first failure.")
@click.option("--show_success", is_flag=True, default=False, help="Show successful outputs")
@click.option(
    "--parallel",
    is_flag=True,
    default=False,
    help="""
    NOT IMPLEMENTED
    Runs all linters marked with parallel_run=True at the same time
    NOTE: All linters labeled as parallel_run=False will be run BEFORE ones marked as True.
    """,
)
@click.option(
    "--ignore_linter_weight", is_flag=True, default=False, help="Ignores linter weight and runs in the order in CONF."
)
@click.option("--language", "-l", default=None, type=Language, help="Specify a language to run linters for.")
def lint(
    check: bool,
    specific: t.List[str],
    fail_fast: bool,
    show_success: bool,
    parallel: bool,
    ignore_linter_weight: bool,
    language: t.Optional[Language],
):  # pylint: disable=too-many-arguments
    """
    Run one or more Linters specified in the CONF file.

    Examples:
    ```bash
    pmt lint
    pmt lint -s black -s flake8
    pmt -rp ./some/path lint
    pmt -n py_mono_tools lint -l python
    ```
    """
    if parallel is True:
        raise NotImplementedError

    logger.info("Starting lint")

    linters_to_run = _filter_linters(specific_linters=specific, language=language)

    if ignore_linter_weight is False:
        linters_to_run.sort(key=lambda x: x.weight, reverse=True)

    for linter in linters_to_run:
        logger.debug("Linting: %s", linter)
        if check is True:
            logs, return_code = linter.check()
        else:
            logs, return_code = linter.run()
        logger.info("Lint result: %s %s", linter.name, return_code)

        if show_success is False and return_code == 0:
            logger.debug("Skipping successful output")
            logger.debug(logs)
        else:
            logger.info(logs)

        if fail_fast is True and return_code != 0:
            logger.error("Linter %s failed with code %s", linter.name, return_code)
            sys.exit(1)

    logger.info("Linting complete")


@cli.command()
def test():
    """Run all the tests specified in the CONF file."""
    testers = consts.CONF.TEST
    for tester in testers:
        logger.info("Testing: %s", tester.name)
        logs, return_code = tester.run()
        logger.info("Test result: %s %s", tester.name, return_code)
        logger.info(logs)


@cli.command()
@click.option("--plan", is_flag=True, default=False)
def deploy(plan: bool):
    """Run the specified build and deploy in the specific CONF file."""
    deployers = consts.CONF.DEPLOY  # type: ignore
    for deployer in deployers:
        logger.info("Deploying: %s", deployer.name)
        if plan is True:
            return_code, logs = deployer.plan()
        else:
            return_code, logs = deployer.run()
        logger.info("Deploy result: %s %s", deployer.name, return_code)
        logger.info(logs)


@cli.command()
def interactive():
    """Drop into an interactive session in your specified backend."""
    consts.CURRENT_BACKEND.interactive()


@cli.command(name="list")
def list_():
    """List all CONF file names and relative paths."""
    conf_names = []
    for rel_path, _, filenames in os.walk("."):
        for filename in filenames:
            if filename == "CONF":
                path = pathlib.Path(rel_path).resolve()
                mod = _load_conf(str(path))
                conf_names.append(f"{mod.NAME} -- {rel_path}")

    print("Backends:")
    for backend in consts.ALL_BACKEND_NAMES:
        print("    " + backend)

    print("CONF file names:")
    for conf_name in conf_names:
        print("    " + conf_name)

    print("Deployers:")
    for deployer in consts.ALL_DEPLOYER_NAMES:
        print("    " + deployer)

    print("Linters:")
    for linter in consts.ALL_LINTER_NAMES:
        print("    " + linter)

    print("Testers:")
    for tester in consts.ALL_TESTER_NAMES:
        print("    " + tester)


# @cli.command()
# @click.option("--force-rebuild", is_flag=True, default=False)
# @click.option("--modules", multiple=True, type=t.List[str], default=["all"])
# def build(force_rebuild, modules):
#     """
#     Run the build process for the specified build system.
#
#     Docker is the default.
#     """
#     logger.info(modules)
#     consts.CURRENT_BACKEND.build(force_rebuild=force_rebuild)
#
#
#
#
# @cli.command()
# def init():
#     """Initialize the current directory with the necessary files."""
#     raise NotImplementedError
#
#
# @cli.group()
# def new():
#     """Create a new module with the specified name."""
#     raise NotImplementedError
#
#
# @new.command()
# def migration():
#     """Generate an Alembic Database migration."""
#     raise NotImplementedError
#
#
# @new.command()
# def package():
#     """Not implemented."""
#     raise NotImplementedError
#
#
# @cli.command()
# def run():
#     """Not implemented."""
#     raise NotImplementedError
#
#
# @cli.command()
# def setup():
#     """Not implemented."""
#     raise NotImplementedError
#
#
# @cli.command()
# def validate():
#     """Not implemented."""
#     raise NotImplementedError
