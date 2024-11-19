# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Configuration migration utilities

Utility for processing loaded configuration files to apply updates for compatibility
"""

import importlib
import inspect
import json
import logging
import os
import yaml
from pathlib import Path


class Migration:
    """Required interface for migrations"""

    def apply(config_dict: dict) -> dict:
        raise NotImplementedError


# list of migrations, should this be dynamically built from the package?
ordered_migrations = []
root_path = Path(__file__).parents[0]
for module_filename in sorted(os.listdir(root_path)):
    if not module_filename.endswith(".py"):
        continue
    if module_filename.startswith("__"):
        continue
    module_name = module_filename.replace(".py", "")
    mod = importlib.import_module(f"{__package__}.{module_name}")
    migrations = [  # Extract only classes with same source package name
        klass
        for _, klass in inspect.getmembers(mod, inspect.isclass)
        if klass.__module__.startswith(mod.__name__) and Migration in klass.__bases__
    ]
    ordered_migrations += migrations


def migrate(source_filename: Path):
    import copy

    # should this just accept a dictionary?
    original_config = None
    # check file for JSON or YAML compatibility
    for loader in (yaml.safe_load, json.load):
        try:
            with open(source_filename) as source_file:
                original_config = loader(source_file)
                break
        except Exception as er:
            msg = f"Configuration file {source_filename} failed to parse as {loader}!"
            logging.debug(msg, exc_info=er)
    if original_config is None:
        logging.error("Could not parse configuration nothing to migrate!")
        return None

    updated_config = copy.deepcopy(original_config)
    for migration in ordered_migrations:
        new_config = migration.apply(updated_config)
        if new_config != updated_config:
            updated_config = new_config
            msg = f"Applied migrations changes from {migration.__name__}"
            logging.info(msg)

    if original_config != updated_config:
        logging.info("Migration preformed")

    return updated_config
