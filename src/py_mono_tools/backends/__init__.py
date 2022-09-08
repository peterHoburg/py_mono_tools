"""
Backends for py_mono_tools.

A Backend is what takes the goals instructions and runs them. This could be the local system, docker, or others.
"""
from py_mono_tools.backends.docker import Docker  # noqa: F401
from py_mono_tools.backends.system import System  # noqa: F401
