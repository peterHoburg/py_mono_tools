"""Contains all the commands that the CLI can execute."""
import importlib
import importlib.machinery
import importlib.util
import logging
import os
import pathlib
import typing as t

import click

from py_mono_build.backends.docker import Docker
from py_mono_build.goals.interface import Linter
from py_mono_build.backends.interface import Backend
from py_mono_build.config import logger

logger.info("Starting main")

EXECUTED_FROM: pathlib.Path = pathlib.Path(os.getcwd())
CURRENT_BACKEND: t.Optional[Backend] = None
BACKENDS: t.Dict[str, t.Type[Backend]] = {Docker.name: Docker}


def _init_logger(verbose: bool):
    if verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)


def _set_absolute_path(absolute_path: str):
    logger.info("Overwriting execution root path: %s", absolute_path)
    global EXECUTED_FROM

    EXECUTED_FROM = pathlib.Path(absolute_path)
    os.chdir(EXECUTED_FROM.resolve())


def _set_relative_path(relative_path: str):
    logger.info("Overwriting execution root path: %s", relative_path)
    global EXECUTED_FROM

    EXECUTED_FROM = EXECUTED_FROM.joinpath(pathlib.Path(relative_path))
    os.chdir(EXECUTED_FROM.resolve())


def _init_backend(_build_system: str):
    logger.debug("Initializing build system: %s", _build_system)
    global CURRENT_BACKEND

    CURRENT_BACKEND = BACKENDS[_build_system](
        execution_root_path=EXECUTED_FROM
    )


@click.group()
@click.option("--backend", default="docker", type=str)
@click.option("--absolute_path", "-ap", default=None, type=click.Path())
@click.option("--relative_path", "-rp", default=None, type=click.Path())
@click.option("--verbose", "-v", default=False, is_flag=True)
def cli(backend, absolute_path, relative_path, verbose):
    """Py mono build is a CLI tool that simplifies using python in a monorepo."""
    logger.info("Starting cli")

    _init_logger(verbose=verbose)

    logger.debug("Executed from: %s", EXECUTED_FROM)
    logger.debug("Current backend: %s", CURRENT_BACKEND)
    logger.debug("Backends: %s", BACKENDS)

    if absolute_path is not None:
        _set_absolute_path(absolute_path=absolute_path)
    elif relative_path is not None:
        _set_relative_path(relative_path=relative_path)

    _init_backend(backend)


@cli.command()
@click.option("--force-rebuild", is_flag=True, default=False)
@click.option("--modules", multiple=True, type=list[str], default=["all"])
def build(force_rebuild, modules):
    """
    Run the build process for the specified build system.

    Docker is the default.
    """
    CURRENT_BACKEND.build(force_rebuild=force_rebuild)


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
def lint(check: bool, specific: t.List[str]):
    """Run one or more Linters specified in the CONF file."""
    logger.info("Starting lint")

    conf_location = f"{EXECUTED_FROM}/CONF"
    logger.debug("CONF location: %s", conf_location)

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    loader.exec_module(mod)

    linters: t.List[Linter] = mod.LINT
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
            result = linter.check()
        else:
            result = linter.run()
        logger.info("Lint result: %s %s", linter.name, result)

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
    raise NotImplementedError


@cli.command()
def run():
    raise NotImplementedError


@cli.command()
def interactive():
    """Drop into an interactive session in your specified backend."""
    raise NotImplementedError


@cli.command()
def setup():
    raise NotImplementedError


@cli.command()
def test():
    """Run all the tests specified in the CONF file."""
    raise NotImplementedError


@cli.command()
def validate():
    raise NotImplementedError
