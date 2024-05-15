# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Functions for working with garak plugins (enumeration, loading, etc)"""

import importlib
import inspect
import logging
import os
from typing import List

from garak import _config


def enumerate_plugins(
    category: str = "probes", skip_base_classes=True
) -> List[tuple[str, bool]]:
    """A function for listing all modules & plugins of the specified kind.

    garak's plugins are organised into four packages - probes, detectors, generators
    and harnesses. Each package contains a base module defining the core plugin
    classes. The other modules in the package define classes that inherit from the
    base module's classes.

    enumerate_plugins() works by first looking at the base module in a package
    and finding the root classes here; it will then go through the other modules
    in the package and see which classes can be enumerated from these.

    :param category: the name of the plugin package to be scanned; should
      be one of probes, detectors, generators, or harnesses.
    :type category: str
    """

    if category not in ("probes", "detectors", "generators", "harnesses", "buffs"):
        raise ValueError("Not a recognised plugin type:", category)

    base_mod = importlib.import_module(f"garak.{category}.base")

    if category == "harnesses":
        root_plugin_classname = "Harness"
    else:
        root_plugin_classname = category.title()[:-1]

    base_plugin_classnames = set(
        [
            n
            for n in dir(base_mod)
            if "__class__" in dir(getattr(base_mod, n))
            and getattr(base_mod, n).__class__.__name__
            == "type"  # be careful with what's imported into base modules
        ]
        + [root_plugin_classname]
    )

    plugin_class_names = []

    for module_filename in sorted(os.listdir(_config.transient.basedir / category)):
        if not module_filename.endswith(".py"):
            continue
        if module_filename.startswith("__"):
            continue
        if module_filename == "base.py" and skip_base_classes:
            continue
        module_name = module_filename.replace(".py", "")
        mod = importlib.import_module(f"garak.{category}.{module_name}")
        module_entries = set(
            [entry for entry in dir(mod) if not entry.startswith("__")]
        )
        if skip_base_classes:
            module_entries = module_entries.difference(base_plugin_classnames)
        module_plugin_names = set()
        for module_entry in module_entries:
            obj = getattr(mod, module_entry)
            if inspect.isclass(obj):
                if obj.__bases__[-1].__name__ in base_plugin_classnames:
                    module_plugin_names.add((module_entry, obj.active))

        for module_plugin_name, active in sorted(module_plugin_names):
            plugin_class_names.append(
                (f"{category}.{module_name}.{module_plugin_name}", active)
            )
    return plugin_class_names


def configure_plugin(plugin_path: str, plugin: object) -> object:
    category, module_name, plugin_class_name = plugin_path.split(".")
    plugin_name = f"{module_name}.{plugin_class_name}"
    plugin_type_config = getattr(_config.plugins, category)
    if plugin_name in plugin_type_config:
        for k, v in plugin_type_config[plugin_name].items():
            setattr(plugin, k, v)
    return plugin


def load_plugin(path, break_on_fail=True) -> object:
    """load_plugin takes a path to a plugin class, and attempts to load that class.
    If successful, it returns an instance of that class.

    :param path: The path to the class to be loaded, e.g. "probes.test.Blank"
    :type path: str
    :param break_on_fail: Should we raise exceptions if there are problems with the load?
      (default is True)
    :type break_on_fail: bool
    """
    try:
        category, module_name, plugin_class_name = path.split(".")
    except ValueError as ve:
        if break_on_fail:
            raise ValueError(
                f'Expected plugin name in format category.module_name.class_name, got "{path}"'
            ) from ve
        else:
            return False
    module_path = f"garak.{category}.{module_name}"
    try:
        mod = importlib.import_module(module_path)
    except Exception as e:
        logging.warning("Exception failed import of %s", module_path)
        if break_on_fail:
            raise ValueError("Didn't successfully import " + module_name) from e
        else:
            return False

    try:
        plugin_instance = getattr(mod, plugin_class_name)()
    except AttributeError as ae:
        logging.warning(
            "Exception failed instantiation of %s.%s", module_path, plugin_class_name
        )
        if break_on_fail:
            raise ValueError(
                f"Plugin {plugin_class_name} not found in {category}.{module_name}"
            ) from ae
        else:
            return False
    except Exception as e:
        # print("error in: module", mod.__name__, "class", plugin_class_name)
        logging.warning(
            "error instantiating module %s class %s", str(mod), plugin_class_name
        )
        if break_on_fail:
            raise Exception(e) from e
        else:
            return False

    plugin_instance = configure_plugin(path, plugin_instance)

    return plugin_instance
