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
from py_mono_tools.goals import linters as linters_mod
from py_mono_tools.goals.interface import Language, Linter


logger.info("Starting main")


def _find_linters():
    logger.debug("Finding linters")
    linter_classes = inspect.getmembers(linters_mod, inspect.isclass)
    linter_instances = [
        linter_class[1]()
        for linter_class in linter_classes
        if issubclass(linter_class[1], Linter) and linter_class[1] != Linter
    ]
    # pylint: disable=invalid-name
    consts.ALL_LINTERS = linter_instances

    for linter in linter_instances:
        consts.ALL_LINTER_NAMES.append(linter.name)

    logger.debug("Found linters: %s", consts.ALL_LINTER_NAMES)


_find_linters()


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

    # pylint: disable=invalid-name
    consts.EXECUTED_FROM = pathlib.Path(absolute_path).resolve()

    os.chdir(consts.EXECUTED_FROM.resolve())  # pylint: disable=invalid-name


def _set_relative_path(relative_path: str):
    logger.info("Overwriting execution root path: %s", relative_path)

    # pylint: disable=invalid-name
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

    # pylint: disable=invalid-name
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

    mod = _load_conf(consts.EXECUTED_FROM)

    # pylint: disable=invalid-name
    consts.CONF = mod
    if backend is None:
        try:
            backend = consts.CONF.BACKEND
        except AttributeError:
            backend = "system"

    logger.info("Using backed: %s", backend)

    _init_backend(backend)


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
def deploy():
    """Run the specified build and deploy in the specific CONF file."""
    deployers = consts.CONF.DEPLOY
    for deployer in deployers:
        logger.info("Deploying: %s", deployer.name)
        logs, return_code = deployer.plan()
        logger.info("Deploy result: %s %s", deployer.name, return_code)
        logger.info(logs)


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
# def interactive():
#     """Drop into an interactive session in your specified backend."""
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
