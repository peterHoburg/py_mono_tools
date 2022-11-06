import inspect
import typing as t

from py_mono_tools.backends import Docker, System
from py_mono_tools.goals import deployers as deployers_mod, linters as linters_mod, testers as testers_mod
from py_mono_tools.goals.interface import Deployer, Language, Linter, Tester
from py_mono_tools.utils.config import cfg, logger


def find_goals():
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
    logger.debug("Initializing build system: %s", _build_system)

    cfg.BACKENDS = {
        Docker.name: Docker,
        System.name: System,
    }

    cfg.CURRENT_BACKEND = cfg.BACKENDS[_build_system]()


def filter_linters(specific_linters: t.List[str], language: t.Optional[Language]) -> t.List[Linter]:
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
