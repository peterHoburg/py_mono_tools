import os
import typing as t
from pathlib import Path

import click

from py_mono_build.helpers.docker import Docker
from py_mono_build.interfaces.base_class import BuildSystem


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

EXECUTION_ROOT_PATH: Path = Path(os.getcwd())
CURRENT_BUILD_SYSTEM: t.Optional[BuildSystem] = None

BUILD_SYSTEMS: t.Dict[str, BuildSystem] = {Docker.name: Docker}
VALIDATORS: t.List
LINTERS: t.List


@click.group()
@click.option("--build-system", default="docker")
@click.option("--execution-root-path", default=None)
def cli(build_system, execution_root_path):
    _get_execution_root_path(execution_root_path_string=execution_root_path)
    _init_build_system(build_system)


def _get_execution_root_path(execution_root_path_string: t.Optional[str] = None):
    if execution_root_path_string is not None:
        global EXECUTION_ROOT_PATH

        EXECUTION_ROOT_PATH = Path(execution_root_path_string)
        os.chdir(EXECUTION_ROOT_PATH.resolve())


def _init_build_system(_build_system: str):
    global CURRENT_BUILD_SYSTEM

    CURRENT_BUILD_SYSTEM = BUILD_SYSTEMS[_build_system](execution_root_path=EXECUTION_ROOT_PATH)


@cli.command()
def build():
    CURRENT_BUILD_SYSTEM.build()


@cli.command()
def deploy():
    pass


@cli.command(name="format")
def format_():
    pass


@cli.command()
def init():
    pass


@cli.command()
def lint():
    pass


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
def setup():
    pass


@cli.command()
def test():
    pass


@cli.command()
def validate():
    pass


if __name__ == '__main__':
    cli(["--execution-root-path", "../amira_clone", "build"])
