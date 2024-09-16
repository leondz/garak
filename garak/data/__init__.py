# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Local read only resources found by precedence matching supported paths

Ideal usage:

```
file_path = resources / "filename"
with open(file_path) as f:
    f.read()
```

Resources that do not have a `shipped` version should wrap path access in a try block:
```
try:
    file_path = resources / "filename"
except GarakException as e:
    logging.warn("No resource file found.", exc_info=e)
```
"""

import pathlib

from garak import _config
from garak.exception import GarakException


class LocalDataPath(pathlib.Path):
    """restricted Path object usable only for existing resource files"""

    ORDERED_SEARCH_PATHS = [
        _config.transient.data_dir / "data",
        _config.transient.package_dir / "data",
    ]

    def joinpath(self, *pathsegments):

        for segment in pathsegments:
            prefix_removed = None
            for path in self.ORDERED_SEARCH_PATHS:
                if (path == self and segment != "..") or path in self.parents:
                    prefix_removed = self.relative_to(path)
                    break
            if prefix_removed is None:
                raise GarakException(
                    f"The requested resource does not refer to a valid path: {self}"
                )
            for path in self.ORDERED_SEARCH_PATHS:
                if segment == "..":
                    projected = (path / prefix_removed).parent
                else:
                    projected = (path / prefix_removed).joinpath(segment)
                if projected.exists():
                    return LocalDataPath(projected)

        raise GarakException(f"The resource requested does not exist {segment}")


path = LocalDataPath(_config.transient.data_dir / "data")
