"""Contains all the commands that the CLI can execute."""
import importlib
import importlib.machinery
import importlib.util
import logging
import os
import pathlib
import sys
import typing as t

import click

from py_mono_build.backends import Docker, System
from py_mono_build.config import consts, logger
from py_mono_build.goals.interface import Linter


logger.info("Starting main")

# TODO have parallel option
# TODO add weight to linters
# TODO run parallel false first by default.
# TODO add shell auto completion for linters: https://click.palletsprojects.com/en/8.1.x/shell-completion/
# TODO load linter confs dynamically


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
    consts.EXECUTED_FROM = consts.EXECUTED_FROM.joinpath(
        pathlib.Path(relative_path).resolve()
    )
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
@click.option("--backend", default="system", type=str)
@click.option("--absolute_path", "-ap", default=None, type=click.Path())
@click.option("--relative_path", "-rp", default=None, type=click.Path())
@click.option("--verbose", "-v", default=False, is_flag=True)
def cli(backend, absolute_path, relative_path, verbose):
    """Py mono build is a CLI tool that simplifies using python in a monorepo."""
    if "--help" in sys.argv or "-h" in sys.argv:
        return

    logger.info("Starting cli")

    _init_logger(verbose=verbose)

    logger.debug("Executed from: %s", consts.EXECUTED_FROM)
    logger.debug("Current backend: %s", consts.CURRENT_BACKEND)
    logger.debug("Backends: %s", consts.BACKENDS)

    if absolute_path is not None:
        _set_absolute_path(absolute_path=absolute_path)
    elif relative_path is not None:
        _set_relative_path(relative_path=relative_path)

    _load_conf()
    _init_backend(backend)


@cli.command()
@click.option("--force-rebuild", is_flag=True, default=False)
@click.option("--modules", multiple=True, type=list[str], default=["all"])
def build(force_rebuild, modules):
    """
    Run the build process for the specified build system.

    Docker is the default.
    """
    print(modules)
    consts.CURRENT_BACKEND.build(force_rebuild=force_rebuild)


@cli.command()
def deploy():
    """Run the specified build and deploy in the specific CONF file."""
    raise NotImplementedError


@cli.command()
def init():
    """Initialize the current directory with the necessary files."""
    raise NotImplementedError


@cli.command()
@click.option("--check", is_flag=True, default=False)
@click.option(
    "--specific",
    "-s",
    multiple=True,
    default=[],
    help="Specify one or more linters to run. NOTE: The linter MUST be listed in the respected CONF file.",
)
@click.option(
    "--fail_fast", "-ff", is_flag=True, default=False, help="Stop on first failure."
)
@click.option(
    "--show_success", is_flag=True, default=False, help="Show successful outputs"
)
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
def lint(
    check: bool,
    specific: t.List[str],
    fail_fast: bool,
    show_success: bool,
    parallel: bool,
):
    """Run one or more Linters specified in the CONF file."""
    if parallel is True:
        raise NotImplementedError

    logger.info("Starting lint")

    linters: t.List[Linter] = consts.CONF.LINT  # type: ignore
    logger.debug("Linters: %s", linters)

    cleaned_spec = []
    for linter_name in specific:
        cleaned_spec.append(linter_name.strip().lower())

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


@cli.group()
def new():
    """Create a new module with the specified name."""
    raise NotImplementedError


@new.command()
def migration():
    """Generate an Alembic Database migration."""
    raise NotImplementedError


@new.command()
def package():
    """Not implemented."""
    raise NotImplementedError


@cli.command()
def run():
    """Not implemented."""
    raise NotImplementedError


@cli.command()
def interactive():
    """Drop into an interactive session in your specified backend."""
    raise NotImplementedError


@cli.command()
def setup():
    """Not implemented."""
    raise NotImplementedError


@cli.command()
def test():
    """Run all the tests specified in the CONF file."""
    raise NotImplementedError


@cli.command()
def validate():
    """Not implemented."""
    raise NotImplementedError
