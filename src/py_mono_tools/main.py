"""Contains all the commands that the CLI can execute."""
import importlib
import importlib.machinery
import importlib.util
import inspect
import logging
import os
import pathlib
import sys
import typing as t

import click

from py_mono_tools.backends import Docker, System
from py_mono_tools.config import consts, logger
from py_mono_tools.goals import linters as linters_mod
from py_mono_tools.goals.interface import Linter


logger.info("Starting main")


def _find_linters():
    logger.debug("Finding linters")
    linter_classes = inspect.getmembers(linters_mod, inspect.isclass)
    linter_instances = [
        linter_class[1]()
        for linter_class in linter_classes
        if issubclass(linter_class[1], Linter) and linter_class[1] != Linter
    ]
    consts.ALL_LINTERS = linter_instances

    for linter in linter_instances:
        consts.ALL_LINTER_NAMES.append(linter.name)

    logger.debug("Found linters: %s", consts.ALL_LINTER_NAMES)


_find_linters()


def _load_conf():
    conf_location = f"{consts.EXECUTED_FROM}/CONF"
    logger.debug("CONF location: %s", conf_location)

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    loader.exec_module(mod)

    # pylint: disable=invalid-name
    consts.CONF = mod


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


def _init_backend(_build_system: str):
    logger.debug("Initializing build system: %s", _build_system)

    # pylint: disable=invalid-name
    consts.BACKENDS = {
        Docker.name: Docker,
        System.name: System,
    }

    consts.CURRENT_BACKEND = consts.BACKENDS[_build_system]()


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
@click.option("--verbose", "-v", default=False, is_flag=True)
def cli(backend, absolute_path, relative_path, verbose):
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

    _load_conf()
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
def lint(
    check: bool,
    specific: t.List[str],
    fail_fast: bool,
    show_success: bool,
    parallel: bool,
    ignore_linter_weight: bool,
):  # pylint: disable=too-many-arguments
    """
Run one or more Linters specified in the CONF file.

Examples:
```bash
pmt lint
pmt lint -s black -s flake8
pmt -rp ./some/path lint
```
    """
    if parallel is True:
        raise NotImplementedError

    logger.info("Starting lint")

    linters: t.List[Linter] = consts.CONF.LINT  # type: ignore
    logger.debug("Linters: %s", linters)

    cleaned_spec = []
    for linter_name in specific:
        cleaned_spec.append(linter_name.strip().lower())
    if ignore_linter_weight is False:
        linters.sort(key=lambda x: x.weight, reverse=True)
    for linter in linters:
        if cleaned_spec and linter.name.strip().lower() not in cleaned_spec:
            logger.debug("Linters requested: %s", cleaned_spec)
            logger.debug("Skipping linter: %s", linter.name)
            continue

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
# @cli.command()
# def deploy():
#     """Run the specified build and deploy in the specific CONF file."""
#     raise NotImplementedError
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
# def test():
#     """Run all the tests specified in the CONF file."""
#     raise NotImplementedError
#
#
# @cli.command()
# def validate():
#     """Not implemented."""
#     raise NotImplementedError
