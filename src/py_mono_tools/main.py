"""Contains all the commands that the CLI can execute."""
import os
import os.path
import pathlib
import sys
import typing as t

import click

from py_mono_tools.config import consts, logger
from py_mono_tools.goals.interface import Language
from py_mono_tools.cli_interface import GoalOutput
from py_mono_tools.utils import (
    init_logger,
    load_conf,
    set_absolute_path,
    set_path_from_conf_name,
    set_relative_path,
)
from py_mono_tools.interface_utils import filter_linters, find_goals, init_backend


find_goals()


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
@click.option("--silent", "-s", default=False, is_flag=True)
@click.option("--machine_output", "-mo", default=False, is_flag=True)
def cli(backend, absolute_path, relative_path, name, verbose, silent, machine_output):
    """Py mono tool is a CLI tool that simplifies using python in a monorepo."""
    if "--help" in sys.argv or "-h" in sys.argv:
        return

    if machine_output is True:
        silent = True
        verbose = False
        consts.USE_MACHINE_OUTPUT = True

    init_logger(verbose=verbose, silent=silent)
    logger.info("Starting py_mono_tools")

    logger.debug("Executed from: %s", consts.EXECUTED_FROM)
    logger.debug("Current backend: %s", consts.CURRENT_BACKEND)
    logger.debug("Backends: %s", consts.BACKENDS)

    if absolute_path is not None:
        set_absolute_path(absolute_path=absolute_path)
    elif relative_path is not None:
        set_relative_path(relative_path=relative_path)
    elif name is not None:
        set_path_from_conf_name(name)

    try:
        mod = load_conf(consts.EXECUTED_FROM)
        consts.CONF = mod
        if backend is None:
            try:
                backend = consts.CONF.BACKEND
            except AttributeError:
                backend = "system"

        logger.info("Using backed: %s", backend)

        init_backend(backend)
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

    linters_to_run = filter_linters(specific_linters=specific, language=language)

    if ignore_linter_weight is False:
        linters_to_run.sort(key=lambda x: x.weight, reverse=True)

    for linter in linters_to_run:
        logger.debug("Linting: %s", linter)
        if check is True:
            logs, return_code = linter.check()
        else:
            logs, return_code = linter.run()

        consts.MACHINE_OUTPUT.goals.append(GoalOutput(name=linter.name, output=logs, returncode=return_code))

        if return_code != 0:
            consts.MACHINE_OUTPUT.returncode = 1

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
    if consts.USE_MACHINE_OUTPUT is True:
        print(consts.MACHINE_OUTPUT.json(indent=2))


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
                mod = load_conf(str(path))
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
