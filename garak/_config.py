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

from dynaconf import Dynaconf

version = -1


@dataclass
class Transient:
    """Object to hold transient global config items not set externally"""

    reportfile = None
    hitlogfile = None
    args = None  # only access this when determining what was passed on CLI
    run_id = None
    basedir = pathlib.Path(__file__).parents[0]
    starttime = None
    starttime_iso = None


transient = Transient()


@dataclass
class StubDataclass:
    pass


system = StubDataclass()
run = StubDataclass()
plugins = StubDataclass()

# this is so popular, let's set a default. what other defaults are worth setting? what's the policy?
run.seed = None

# placeholder
# generator, probe, detector, buff = {}, {}, {}, {}


def _set_settings(config_obj, settings_obj: dict):
    for k, v in settings_obj.items():
        setattr(config_obj, k, v)
    return config_obj


def _store_config(settings_files):
    global system, run, plugins
    settings = Dynaconf(settings_files=settings_files, apply_default_on_none=True)
    system = _set_settings(system, settings.system)
    run = _set_settings(system, settings.run)
    plugins = _set_settings(system, settings.plugins)


def load_base_config():
    settings_files = [str(transient.basedir / "resources/garak.core.yaml")]
    _store_config(settings_files=settings_files)


def load_config(site_config_filename="garak.site.yaml", run_config_filename=None):
    # would be good to bubble up things from run_config, e.g. generator, probe(s), detector(s)
    # and then not have cli be upset when these are not given as cli params
    global system, run, plugins

    settings_files = [str(transient.basedir / "resources/garak.core.yaml")]
    fq_site_config_filename = str(transient.basedir / site_config_filename)
    if os.path.isfile(fq_site_config_filename):
        settings_files.append(fq_site_config_filename)
    else:
        # warning, not error, because this one has a default value
        logging.warning("site config not found: %s", fq_site_config_filename)

    if run_config_filename is not None:
        fq_run_config_filename = str(transient.basedir / run_config_filename)
        if os.path.isfile(fq_run_config_filename):
            settings_files.append(fq_run_config_filename)
        else:
            logging.error("run config not found: %s", fq_run_config_filename)

    logging.debug("Loading configs from: %s", ",".join(settings_files))
    _store_config(settings_files=settings_files)
