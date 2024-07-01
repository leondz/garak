# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Functions for working with garak plugins (enumeration, loading, etc)"""

import importlib
import inspect
import json
import logging
import shutil
import os
from typing import List, Callable, Union
from pathlib import Path

from garak import _config
from garak.exception import GarakException

PLUGIN_TYPES = ("probes", "detectors", "generators", "harnesses", "buffs")
PLUGIN_CLASSES = ("Probe", "Detector", "Generator", "Harness", "Buff")


class PluginEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)  # allow set as list
        if isinstance(obj, Path):
            # relative path for now, may be better to suppress `Path` objects
            return str(obj).replace(str(_config.transient.basedir), "")
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            logging.debug("Attempt to serialize JSON skipped: %s", e)
            return None  # skip items that cannot be serialized at this time


class _PluginCache:
    _plugin_cache_file = _config.transient.basedir / "resources" / "plugin_cache.json"
    _user_plugin_cache_file = _plugin_cache_file
    _plugin_cache_dict = None

    def __init__(self) -> None:
        if self._plugin_cache_dict is None:
            self._plugin_cache_dict = self._load_plugin_cache()

    @staticmethod
    def _extract_modules_klasses(base_klass):
        return [  # Extract only classes with same source package name
            name
            for name, klass in inspect.getmembers(base_klass, inspect.isclass)
            if klass.__module__.startswith(base_klass.__name__)
        ]

    def _load_plugin_cache(self):
        if not os.path.exists(self._plugin_cache_file):
            self._build_plugin_cache()
        if not os.path.exists(self._user_plugin_cache_file):
            shutil.copy2(self._plugin_cache_file, self._user_plugin_cache_file)
        with open(self._user_plugin_cache_file, "r", encoding="utf-8") as cache_file:
            local_cache = json.load(cache_file)
            return local_cache

    def _build_plugin_cache(self):
        # this method writes only to the user's cache
        local_cache = {}

        for plugin_type in PLUGIN_TYPES:
            plugin_dict = {}
            for plugin in self._enumerate_plugin_klasses(plugin_type):
                plugin_name = ".".join([plugin.__module__, plugin.__name__]).replace(
                    "garak.", ""
                )
                plugin_dict[plugin_name] = self.plugin_info(plugin)
            local_cache[plugin_type] = plugin_dict

        with open(self._user_plugin_cache_file, "w", encoding="utf-8") as cache_file:
            json.dump(local_cache, cache_file, cls=PluginEncoder, indent=2)

    def _enumerate_plugin_klasses(self, category: str) -> List[Callable]:
        if category not in PLUGIN_TYPES:
            raise ValueError("Not a recognised plugin type:", category)

        base_mod = importlib.import_module(f"garak.{category}.base")

        base_plugin_classnames = set(self._extract_modules_klasses(base_mod))

        module_plugin_names = set()

        for module_filename in sorted(os.listdir(_config.transient.basedir / category)):
            if not module_filename.endswith(".py"):
                continue
            if module_filename.startswith("__"):
                continue
            module_name = module_filename.replace(".py", "")
            mod = importlib.import_module(
                f"garak.{category}.{module_name}"
            )  # import here will access all namespace level imports consider a cache to speed up processing
            module_entries = set(self._extract_modules_klasses(mod))

            for module_entry in module_entries:
                obj = getattr(mod, module_entry)
                for interface in base_plugin_classnames:
                    klass = getattr(base_mod, interface)
                    if issubclass(obj, klass):
                        module_plugin_names.add(obj)

        return module_plugin_names

    def instance(self) -> dict:
        return self._plugin_cache_dict

    def plugin_info(self, plugin: Union[Callable, str]) -> dict:
        if isinstance(plugin, str):
            plugin_name = plugin
            category = plugin_name.split(".")[0]

            _plugin_cache = self._load_plugin_cache()
            plugin_metadata = _plugin_cache[category].get(plugin_name, {})
            if len(plugin_metadata) > 0:
                return plugin_metadata
            else:
                # the requested plugin is not cached import the class for eval
                parts = plugin.split(".")
                match len(parts):
                    case 2:
                        module = ".".join(parts[:-1])
                        klass = parts[-1]
                        imported_module = importlib.import_module(f"garak.{module}")
                        plugin = getattr(imported_module, klass)
                    case _:
                        raise ValueError
        else:
            plugin_name = ".".join([plugin.__module__, plugin.__name__]).replace(
                "garak.", ""
            )

        try:
            plugin_metadata = {}
            priority_fields = ["description"]
            skip_fields = [
                "prompts",
                "triggers",
                "encoding_funcs",  # encoding_funcs are functions
            ]
            # print the attribs it has
            for v in priority_fields:
                if hasattr(plugin, v):
                    plugin_metadata[v] = getattr(plugin, v)
            for v in sorted(dir(plugin)):
                if v in priority_fields or v in skip_fields:
                    continue
                value = getattr(plugin, v)
                if (
                    v.startswith("_")
                    or inspect.ismethod(value)
                    or inspect.isfunction(value)
                ):
                    continue
                if isinstance(value, set):
                    continue
                plugin_metadata[v] = value

        except ValueError as e:
            logging.exception(e)
        except Exception as e:
            logging.error(f"Plugin {plugin_name} not found.")
            logging.exception(e)

        return plugin_metadata


_plugin_cache = _PluginCache()


def plugin_info(plugin: Union[Callable, str]) -> dict:
    return _plugin_cache.plugin_info(plugin)


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

    base_plugin_classnames = set(_PluginCache._extract_modules_klasses(base_mod))

    plugin_class_names = set()

    for k, v in _plugin_cache.instance()[category].items():
        if skip_base_classes and k in base_plugin_classnames:
            continue
        enum_entry = (k, v["active"])
        plugin_class_names.add(enum_entry)

    return plugin_class_names


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
        match len(parts):
            case 2:
                category, module_name = parts
                generator_mod = importlib.import_module(
                    f"garak.{category}.{module_name}"
                )
                if generator_mod.DEFAULT_CLASS:
                    plugin_class_name = generator_mod.DEFAULT_CLASS
                else:
                    raise ValueError(
                        f"module {module_name} has no default class; pass module.ClassName to model_type"
                    )
            case 3:
                category, module_name, plugin_class_name = parts
            case _:
                raise ValueError(
                    f"Attempted to load {path} with unexpected number of tokens."
                )
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
        klass = getattr(mod, plugin_class_name)
        if "config_root" not in inspect.signature(klass.__init__).parameters:
            raise AttributeError(
                'Incompatible function signature: "config_root" is incompatible with this plugin'
            )
        plugin_instance = klass(config_root=config_root)
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
            raise GarakException(e) from e
        else:
            return False

    return plugin_instance
