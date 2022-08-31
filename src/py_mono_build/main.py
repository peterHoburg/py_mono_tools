import importlib
import importlib.machinery
import importlib.util
import logging
import os
import pathlib
import typing as t

import click

from py_mono_build.helpers.docker import Docker
from py_mono_build.interfaces.base_class import BuildSystem, Linter


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting main")

EXECUTED_FROM: pathlib.Path = pathlib.Path(os.getcwd())
logger.debug(f"Executed from: {EXECUTED_FROM}")

CURRENT_BUILD_SYSTEM: t.Optional[BuildSystem] = None
logger.debug(f"Current build system: {CURRENT_BUILD_SYSTEM}")

BUILD_SYSTEMS: t.Dict[str, BuildSystem] = {Docker.name: Docker}
logger.debug(f"Build systems: {BUILD_SYSTEMS}")


@click.group()
@click.option("--build_system", default="docker", type=str)
@click.option("--absolute_path", "-ap", default=None, type=click.Path())
@click.option("--relative_path", "-rp", default=None, type=click.Path())
def cli(build_system, absolute_path, relative_path):
    logger.debug("Starting cli")

    if absolute_path is not None:
        _set_absolute_path(absolute_path=absolute_path)
    elif relative_path is not None:
        _set_relative_path(relative_path=relative_path)

    _init_build_system(build_system)


def _set_absolute_path(absolute_path: t.Optional[str] = None):
    logger.info(f"Overwriting execution root path: {absolute_path}")
    global EXECUTED_FROM

    EXECUTED_FROM = pathlib.Path(absolute_path)
    os.chdir(EXECUTED_FROM.resolve())


def _set_relative_path(relative_path: t.Optional[str] = None):
    logger.info(f"Overwriting execution root path: {relative_path}")
    global EXECUTED_FROM

    EXECUTED_FROM = EXECUTED_FROM.joinpath(pathlib.Path(relative_path))
    os.chdir(EXECUTED_FROM.resolve())


def _init_build_system(_build_system: str):
    logger.debug(f"Initializing build system: {_build_system}")
    global CURRENT_BUILD_SYSTEM

    CURRENT_BUILD_SYSTEM = BUILD_SYSTEMS[_build_system](
        execution_root_path=EXECUTED_FROM
    )


@cli.command()
@click.option("--force-rebuild", is_flag=True, default=False)
@click.option("--modules", multiple=True, type=list[str], default=["all"])
def build(force_rebuild, modules):
    CURRENT_BUILD_SYSTEM.build(force_rebuild=force_rebuild)


@cli.command()
def deploy():
    pass


@cli.command()
def init():
    pass


@cli.command()
@click.option("--check", is_flag=True, default=False)
def lint(check: bool):
    logger.info("Starting lint")

    conf_location = f"{EXECUTED_FROM}/CONF"
    logger.debug(f"CONF location: {conf_location}")

    loader = importlib.machinery.SourceFileLoader("CONF", conf_location)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)

    linters: t.List[Linter] = mod.LINT
    logger.debug(f"Linters: {linters}")

    for linter in linters:
        logger.debug(f"Linting: {linter}")
        if check is True:
            linter.check()
        else:
            linter.run()

    logger.info("Linting complete")


@cli.group()
def new():
    pass


@new.command()
def migration():
    pass


@new.command()
def package():
    pass


@cli.command()
def run():
    pass


@cli.command()
def interactive():
    CURRENT_BUILD_SYSTEM.interactive()


@cli.command()
def setup():
    pass


@cli.command()
def test():
    pass


@cli.command()
def validate():
    pass
