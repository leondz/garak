"""garak global config"""

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# plugin code < base config < site config < run config < cli params

# logging should be set up before config is loaded

from collections import defaultdict
from dataclasses import dataclass
import importlib
import logging
import os
import pathlib
from typing import List
import yaml
from xdg_base_dirs import (
    xdg_cache_home,
    xdg_config_home,
    xdg_data_home,
)
from garak.translator import SimpleTranslator, EncodingTranslator, GoodsideTranslator, DanTranslator, ReverseTranslator
from garak.translator import LocalDanTranslator, LocalTranslator, LocalEncodingTranslator, LocalGoodsideTranslator, LocalReverseTranslator

DICT_CONFIG_AFTER_LOAD = False

version = -1  # eh why this is here? hm. who references it

system_params = (
    "verbose narrow_output parallel_requests parallel_attempts skip_unknown".split()
)
run_params = "seed deprefix eval_threshold generations probe_tags interactive".split()
plugins_params = "model_type model_name extended_detectors".split()
reporting_params = "taxonomy report_prefix".split()
project_dir_name = "garak"


loaded = False


@dataclass
class GarakSubConfig:
    pass


@dataclass
class BuffManager:
    """class to store instantiated buffs"""

    buffs = []


@dataclass
class TransientConfig(GarakSubConfig):
    """Object to hold transient global config items not set externally"""

    report_filename = None
    reportfile = None
    hitlogfile = None
    args = None  # only access this when determining what was passed on CLI
    run_id = None
    package_dir = pathlib.Path(__file__).parents[0]
    config_dir = xdg_config_home() / project_dir_name
    data_dir = xdg_data_home() / project_dir_name
    cache_dir = xdg_cache_home() / project_dir_name
    starttime = None
    starttime_iso = None

    # initialize the user home and cache paths if they do not exist
    config_dir.mkdir(mode=0o740, parents=True, exist_ok=True)
    data_dir.mkdir(mode=0o740, parents=True, exist_ok=True)
    cache_dir.mkdir(mode=0o740, parents=True, exist_ok=True)


transient = TransientConfig()

system = GarakSubConfig()
run = GarakSubConfig()
plugins = GarakSubConfig()
reporting = GarakSubConfig()


def _lock_config_as_dict():
    global plugins
    for plugin_type in ("probes", "generators", "buffs", "detectors", "harnesses"):
        setattr(plugins, plugin_type, _crystallise(getattr(plugins, plugin_type)))


def _crystallise(d):
    for k in d.keys():
        if isinstance(d[k], defaultdict):
            d[k] = _crystallise(d[k])
    return dict(d)


def _nested_dict():
    return defaultdict(nested_dict)


nested_dict = _nested_dict

plugins.probes = nested_dict()
plugins.generators = nested_dict()
plugins.detectors = nested_dict()
plugins.buffs = nested_dict()
plugins.harnesses = nested_dict()
reporting.taxonomy = None  # set here to enable report_digest to be called directly

buffmanager = BuffManager()

config_files = []

# this is so popular, let's set a default. what other defaults are worth setting? what's the policy?
run.seed = None

# placeholder
# generator, probe, detector, buff = {}, {}, {}, {}


def _set_settings(config_obj, settings_obj: dict):
    for k, v in settings_obj.items():
        setattr(config_obj, k, v)
    return config_obj


def _combine_into(d: dict, combined: dict) -> None:
    for k, v in d.items():
        if isinstance(v, dict):
            _combine_into(v, combined.setdefault(k, nested_dict()))
        else:
            combined[k] = v
    return combined


def _load_yaml_config(settings_filenames) -> dict:
    global config_files
    config_files += settings_filenames
    config = nested_dict()
    for settings_filename in settings_filenames:
        with open(settings_filename, encoding="utf-8") as settings_file:
            settings = yaml.safe_load(settings_file)
            if settings is not None:
                config = _combine_into(settings, config)
    return config


def _store_config(settings_files) -> None:
    global system, run, plugins, reporting
    settings = _load_yaml_config(settings_files)
    system = _set_settings(system, settings["system"])
    run = _set_settings(run, settings["run"])
    plugins = _set_settings(plugins, settings["plugins"])
    reporting = _set_settings(reporting, settings["reporting"])


def load_base_config() -> None:
    global loaded
    settings_files = [str(transient.package_dir / "resources" / "garak.core.yaml")]
    logging.debug("Loading configs from: %s", ",".join(settings_files))
    _store_config(settings_files=settings_files)
    loaded = True


def load_config(
    site_config_filename="garak.site.yaml", run_config_filename=None
) -> None:
    # would be good to bubble up things from run_config, e.g. generator, probe(s), detector(s)
    # and then not have cli be upset when these are not given as cli params
    global loaded

    settings_files = [str(transient.package_dir / "resources" / "garak.core.yaml")]

    fq_site_config_filename = str(transient.config_dir / site_config_filename)
    if os.path.isfile(fq_site_config_filename):
        settings_files.append(fq_site_config_filename)
    else:
        # warning, not error, because this one has a default value
        logging.debug("no site config found at: %s", fq_site_config_filename)

    if run_config_filename is not None:
        # take config file path as provided
        if os.path.isfile(run_config_filename):
            settings_files.append(run_config_filename)
        elif os.path.isfile(
            str(transient.package_dir / "configs" / (run_config_filename + ".yaml"))
        ):
            settings_files.append(
                str(transient.package_dir / "configs" / (run_config_filename + ".yaml"))
            )
        else:
            message = f"run config not found: {run_config_filename}"
            logging.error(message)
            raise FileNotFoundError(message)

    logging.debug("Loading configs from: %s", ",".join(settings_files))
    _store_config(settings_files=settings_files)
    if DICT_CONFIG_AFTER_LOAD:
        _lock_config_as_dict()
    loaded = True


def parse_plugin_spec(
    spec: str, category: str, probe_tag_filter: str = ""
) -> tuple[List[str], List[str]]:
    from garak._plugins import enumerate_plugins

    if spec is None or spec.lower() in ("", "auto", "none"):
        return [], []
    unknown_plugins = []
    if spec.lower() in ("all", "*"):
        plugin_names = [
            name
            for name, active in enumerate_plugins(category=category)
            if active is True
        ]
    else:
        plugin_names = []
        for clause in spec.split(","):
            if clause.count(".") < 1:
                found_plugins = [
                    p
                    for p, a in enumerate_plugins(category=category)
                    if p.startswith(f"{category}.{clause}.") and a is True
                ]
                if len(found_plugins) > 0:
                    plugin_names += found_plugins
                else:
                    unknown_plugins += [clause]
            else:
                # validate the class exists
                found_plugins = [
                    p
                    for p, a in enumerate_plugins(category=category)
                    if p == f"{category}.{clause}"
                ]
                if len(found_plugins) > 0:
                    plugin_names += found_plugins
                else:
                    unknown_plugins += [clause]

    if probe_tag_filter is not None and len(probe_tag_filter) > 1:
        plugins_to_skip = []
        for plugin_name in plugin_names:
            plugin_module_name = ".".join(plugin_name.split(".")[:-1])
            plugin_class_name = plugin_name.split(".")[-1]
            m = importlib.import_module(f"garak.{plugin_module_name}")
            c = getattr(m, plugin_class_name)
            if not any([tag.startswith(probe_tag_filter) for tag in c.tags]):
                plugins_to_skip.append(
                    plugin_name
                )  # using list.remove doesn't update for-loop position

        for plugin_to_skip in plugins_to_skip:
            plugin_names.remove(plugin_to_skip)

    return plugin_names, unknown_plugins

def load_translator(translation_service: str="", classname: str="") -> object:
    translator = None
    if translation_service == "local":
        if classname == "encoding":
            translator = LocalEncodingTranslator(plugins.generators)
        elif classname == "goodside":
            translator = LocalGoodsideTranslator(plugins.generators)
        elif classname == "dan":
            translator = LocalDanTranslator(plugins.generators)
        elif classname == "reverse":
            translator = LocalReverseTranslator(plugins.generators)
        else:
            translator = LocalTranslator(plugins.generators)
    elif translation_service == "deepl" or translation_service == "nim":
        if classname == "encoding":
            translator = EncodingTranslator(plugins.generators)
        elif classname == "goodside":
            translator = GoodsideTranslator(plugins.generators)
        elif classname == "dan":
            translator = DanTranslator(plugins.generators)
        elif classname == "reverse":
            translator = ReverseTranslator(plugins.generators)
        else:
            translator = SimpleTranslator(plugins.generators)
    return translator
