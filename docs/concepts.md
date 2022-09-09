
### CONF File
A `CONF` file tells PMT what to do, where to do it, and any arguments to pass to the underlying goals.
A `CONF` file is a python file that imports from py_mono_tools.

Example CONF file that uses the default python linters:
```python
#!/user/bin/env python
# -*- coding: utf-8 -*-
import pathlib

from py_mono_tools.goals.linters import DEFAULT_PYTHON


path = pathlib.Path(__file__).parent

NAME = "Example"
BACKEND = "system"

LINT = [
    *DEFAULT_PYTHON,
]
TEST = []
DEPLOY = []
```

Example CONF file that specifies 3 python linters, and adds arguments:
```python
#!/user/bin/env python
# -*- coding: utf-8 -*-
import pathlib

from py_mono_tools.goals.linters import Black, Flake8, Mypy


path = pathlib.Path(__file__).parent

NAME = "Example"
BACKEND = "system"

LINT = [
    Black(args=["--line-length=120"]),
    Flake8(args=["--ignore=E203", "--ignore=W503"]),
    Mypy(),
]
TEST = []
DEPLOY = []
```

#### Specify CONF file

PMT runs from CONF files. There are 4 ways to specify which CONF file PMT should use.

##### Current directory
`pmt ...`

Runs PMT in the current directory.

##### Relative path
`pmt -rp <relative_path> ...`

Relative path allows you to run PMT from any directory and have it execute in a sub/parent directory.

##### Absolute path
`pmt -ap <absolute_path> ...`

Absolute Path. The user running PMT must have read/write access to the directory specified by the absolute path.

##### CONF file name
`pmt -cf <NAME_in_CONF_file> ...`

The `-cf` takes the `NAME = "<name>"` variable specified in the CONF file.
PMT searches for CONF file names ONLY when the `-cf` flag is used.

NOTE: ONLY the current and child directories will be searched for CONF file NAMEs!

#### Required Variables
There are 4 required variables in a `CONF` file. These can be left as a default value (as seen below),
and nothing will be run.
```python
NAME = ""
LINT: list[type(Linter)] = []
TEST = []
DEPLOY = []
```

##### NAME
`pmt -cf <NAME> lint -s black`

NAME tells PMT what CONF file to run if you execute PMT using a name.


##### LINT
`pmt lint`

The `LINT` variable is a list of goals that inherit from the `py_mono_tools.goals.interface.Linter` class.

##### TEST

##### DEPLOY

#### Optional Variables
```python
Optionally:
```python
PATH = ""
BACKEND = ""
```

##### PATH

##### BACKEND

### Backends

The PMT backend is what takes the goal and runs it. The backend could be the local system or Docker.

The Backend defaults to `system`.
It can be set using the `pmt --backend` flag, or `BACKEND = "<system,docker>"` in a CONF file.

### Goals

#### LINT

A linter is a class that inherits from `py_mono_tools.goals.interface.Linter` ABC. Linters can do many things.
Check formatting (black), check for unused imports (flake8), check for type hints (mypy), etc. Some linters may change
the code (black), while others just check for errors (flake8). Passing the `--check` flag will force all inters to
only check, and not change anything.

Please see the [CLI Reference section for more details](cli.md#lint).
