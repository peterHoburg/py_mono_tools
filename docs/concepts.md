### CONF File

Example CONF file:
```python
#!/user/bin/env python
# -*- coding: utf-8 -*-
import pathlib

from py_mono_tools.goals.linters import DEFAULT_PYTHON


path = pathlib.Path(__file__).parent

NAME = "py_mono_tools"
BACKEND = "system"

LINT = [
    *DEFAULT_PYTHON,
]
TEST = []
DEPLOY = []

```

### Backends

The PMT backend is what takes the goal and runs it. The backend could be the local system or Docker.

The Backend defaults to `system`.
It can be set using the `--backend` flag, or `BACKEND = "<system,docker>"` in a CONF file.


### Goals
