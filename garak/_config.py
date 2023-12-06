#!/usr/bin/env python3
"""garak global config"""

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# plugin code < base config < site config < run config < cli params

# logging should be set up before config is loaded

from dataclasses import dataclass
import logging
import os
import pathlib
from typing import List
import yaml

version = -1  # eh why this is here? hm. who references it

system_params = (
    "verbose report_prefix narrow_output parallel_requests parallel_attempts".split()
)
run_params = "seed deprefix eval_threshold generations".split()
plugins_params = "model_type model_name extended_detectors".split()


loaded = False


@dataclass
class GarakSubConfig:
    pass


@dataclass
class TransientConfig(GarakSubConfig):
    """Object to hold transient global config items not set externally"""

    report_filename = None
    reportfile = None
    hitlogfile = None
    args = None  # only access this when determining what was passed on CLI
    run_id = None
    basedir = pathlib.Path(__file__).parents[0]
    starttime = None
    starttime_iso = None


transient = TransientConfig()

system = GarakSubConfig()
run = GarakSubConfig()
plugins = GarakSubConfig()
plugins.probes = {}
plugins.generators = {}
plugins.detectors = {}
plugins.buffs = {}
plugins.harnesses = {}

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
            _combine_into(v, combined.setdefault(k, {}))
        else:
            combined[k] = v
    return combined


def _load_yaml_config(settings_filenames) -> dict:
    config = {}
    for settings_filename in settings_filenames:
        settings = yaml.safe_load(open(settings_filename, encoding="utf-8"))
        if settings is not None:
            config = _combine_into(settings, config)
    return config


def _store_config(settings_files) -> None:
    global system, run, plugins
    settings = _load_yaml_config(settings_files)
    system = _set_settings(system, settings["system"])
    run = _set_settings(run, settings["run"])
    plugins = _set_settings(plugins, settings["plugins"])


def load_base_config() -> None:
    global loaded
    settings_files = [str(transient.basedir / "resources/garak.core.yaml")]
    logging.debug("Loading configs from: %s", ",".join(settings_files))
    _store_config(settings_files=settings_files)
    loaded = True


def load_config(
    site_config_filename="garak.site.yaml", run_config_filename=None
) -> None:
    # would be good to bubble up things from run_config, e.g. generator, probe(s), detector(s)
    # and then not have cli be upset when these are not given as cli params
    global loaded

    settings_files = [str(transient.basedir / "resources/garak.core.yaml")]

    fq_site_config_filename = str(transient.basedir / site_config_filename)
    if os.path.isfile(fq_site_config_filename):
        settings_files.append(fq_site_config_filename)
    else:
        # warning, not error, because this one has a default value
        logging.warning("site config not found: %s", fq_site_config_filename)

    if run_config_filename is not None:
        # take config file path as provided
        if os.path.isfile(run_config_filename):
            settings_files.append(run_config_filename)
        else:
            logging.error("run config not found: %s", run_config_filename)

    logging.debug("Loading configs from: %s", ",".join(settings_files))
    _store_config(settings_files=settings_files)
    loaded = True


def parse_plugin_spec(spec: str, category: str) -> List[str]:
    from garak._plugins import enumerate_plugins

    if spec is None or spec.lower() in ("", "auto", "none"):
        return []
    if spec.lower() == "all":
        plugin_names = [
            name
            for name, active in enumerate_plugins(category=category)
            if active is True
        ]
    else:
        plugin_names = []
        for clause in spec.split(","):
            if clause.count(".") < 1:
                plugin_names += [
                    p
                    for p, a in enumerate_plugins(category=category)
                    if p.startswith(f"{category}.{clause}.") and a is True
                ]
            else:
                plugin_names += [f"{category}.{clause}"]  # spec parsing

    return plugin_names
