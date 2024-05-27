# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Functions for working with garak plugins (enumeration, loading, etc)"""

import importlib
import inspect
import logging
import os
from typing import List

from garak import _config

PLUGIN_TYPES = ("probes", "detectors", "generators", "harnesses", "buffs")
PLUGIN_CLASSES = ("Probe", "Detector", "Generator", "Harness", "Buff")


@staticmethod
def _extract_modules_klasses(base_klass):
    return [  # Extract only classes with same source package name
        name
        for name, klass in inspect.getmembers(base_klass, inspect.isclass)
        if klass.__module__.startswith(base_klass.__name__)
    ]


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

    if category not in PLUGIN_TYPES:
        raise ValueError("Not a recognised plugin type:", category)

    base_mod = importlib.import_module(f"garak.{category}.base")

    base_plugin_classnames = set(_extract_modules_klasses(base_mod))

    plugin_class_names = []

    for module_filename in sorted(os.listdir(_config.transient.basedir / category)):
        if not module_filename.endswith(".py"):
            continue
        if module_filename.startswith("__"):
            continue
        if module_filename == "base.py" and skip_base_classes:
            continue
        module_name = module_filename.replace(".py", "")
        mod = importlib.import_module(
            f"garak.{category}.{module_name}"
        )  # import here will access all namespace level imports consider a cache to speed up processing
        module_entries = set(_extract_modules_klasses(mod))
        if skip_base_classes:
            module_entries = module_entries.difference(base_plugin_classnames)
        module_plugin_names = set()
        for module_entry in module_entries:
            obj = getattr(mod, module_entry)
            for interface in base_plugin_classnames:
                klass = getattr(base_mod, interface)
                if issubclass(obj, klass):
                    module_plugin_names.add((module_entry, obj.active))

        for module_plugin_name, active in sorted(module_plugin_names):
            plugin_class_names.append(
                (f"{category}.{module_name}.{module_plugin_name}", active)
            )
    return plugin_class_names


def configure_plugin(plugin_path: str, plugin: object, config_root: _config) -> object:
    local_root = config_root.plugins if hasattr(config_root, "plugins") else config_root
    category, module_name, plugin_class_name = plugin_path.split(".")
    plugin_name = f"{module_name}.{plugin_class_name}"
    plugin_type_config = getattr(local_root, category)
    if plugin_name in plugin_type_config:
        for k, v in plugin_type_config[plugin_name].items():
            setattr(plugin, k, v)
    return plugin


def load_plugin(path, break_on_fail=True, config_root=_config) -> object:
    """load_plugin takes a path to a plugin class, and attempts to load that class.
    If successful, it returns an instance of that class.

    :param path: The path to the class to be loaded, e.g. "probes.test.Blank"
    :type path: str
    :param break_on_fail: Should we raise exceptions if there are problems with the load?
      (default is True)
    :type break_on_fail: bool
    """
    try:
        parts = path.split(".")
        category = parts[0]
        module_name = parts[1]
        if len(parts) != 3:
            generator_mod = importlib.import_module(f"garak.{category}.{module_name}")
            if generator_mod.DEFAULT_CLASS:
                plugin_class_name = generator_mod.DEFAULT_CLASS
                path = f"{path}.{plugin_class_name}"
            else:
                raise Exception(
                    "module {module_name} has no default class; pass module.ClassName to model_type"
                )
        else:
            plugin_class_name = parts[2]
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
        from garak.configurable import Configurable

        if issubclass(getattr(mod, plugin_class_name), Configurable):
            plugin_instance = getattr(mod, plugin_class_name)(config_root=config_root)
        else:
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

    plugin_instance = configure_plugin(path, plugin_instance, config_root)

    return plugin_instance
