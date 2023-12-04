#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Definitions of commands and actions that can be run in the garak toolkit"""

import logging
import json


def start_logging():
    logging.basicConfig(
        filename="garak.log",
        level=logging.DEBUG,
        format="%(asctime)s  %(levelname)s  %(message)s",
    )

    # garaklogger = logging.FileHandler("garak.log", encoding="utf-8")
    # garakformatter = logging.Formatter("%(asctime)s  %(levelname)s  %(message)s")
    # garaklogger.setFormatter(garakformatter)
    # garaklogger.setLevel(logging.DEBUG)

    # rootlogger = logging.getLogger()
    # for h in rootlogger.handlers[:]:
    #    rootlogger.removeHandler(h)
    # rootlogger.addHandler(garaklogger)
    # logging.root = rootlogger
    logging.info("invoked")


def start_run(args):
    import logging
    import uuid

    from garak import _config

    logging.info("started at %s", _config.transient.starttime_iso)
    # print("ASSIGN UUID", args)
    _config.transient.run_id = str(uuid.uuid4())  # uuid1 is safe but leaks host info
    if not _config.system.report_prefix:
        _config.transient.report_filename = (
            f"garak.{_config.transient.run_id}.report.jsonl"
        )
    else:
        _config.transient.report_filename = (
            _config.system.report_prefix + ".report.jsonl"
        )
    _config.transient.reportfile = open(
        _config.transient.report_filename, "w", buffering=1, encoding="utf-8"
    )
    args.__dict__.update({"entry_type": "start_run args config"})
    _config.transient.reportfile.write(json.dumps(args.__dict__) + "\n")
    _config.transient.reportfile.write(
        json.dumps(
            {
                "entry_type": "init",
                "garak_version": _config.version,
                "start_time": _config.transient.starttime_iso,
                "run": _config.transient.run_id,
            }
        )
        + "\n"
    )
    logging.info("reporting to %s", _config.transient.report_filename)


def end_run():
    import datetime
    import logging

    from garak import _config

    logging.info("run complete, ending")
    _config.transient.reportfile.close()
    print(f"📜 report closed :) {_config.transient.report_filename}")
    if _config.transient.hitlogfile:
        _config.transient.hitlogfile.close()

    timetaken = (datetime.datetime.now() - _config.transient.starttime).total_seconds()

    msg = f"garak done: complete in {timetaken:.2f}s"
    print(f"✔️  {msg}")
    logging.info(msg)


def print_plugins(prefix: str, color):
    from colorama import Style

    from garak._plugins import enumerate_plugins

    plugin_names = enumerate_plugins(category=prefix)
    plugin_names = [(p.replace(f"{prefix}.", ""), a) for p, a in plugin_names]
    module_names = set([(m.split(".")[0], True) for m, a in plugin_names])
    plugin_names += module_names
    for plugin_name, active in sorted(plugin_names):
        print(f"{Style.BRIGHT}{color}{prefix}: {Style.RESET_ALL}", end="")
        print(plugin_name, end="")
        if "." not in plugin_name:
            print(" 🌟", end="")
        if not active:
            print(" 💤", end="")
        print()


def print_probes():
    from colorama import Fore

    print_plugins("probes", Fore.LIGHTYELLOW_EX)


def print_detectors():
    from colorama import Fore

    print_plugins("detectors", Fore.LIGHTBLUE_EX)


def print_generators():
    from colorama import Fore

    print_plugins("generators", Fore.LIGHTMAGENTA_EX)


def print_buffs():
    from colorama import Fore

    print_plugins("buffs", Fore.LIGHTGREEN_EX)


# describe plugin
def plugin_info(plugin_name):
    import inspect

    from garak._plugins import load_plugin

    # load plugin
    try:
        plugin = load_plugin(plugin_name)
        print(f"Configured info on {plugin_name}:")
        priority_fields = ["description"]
        skip_fields = ["prompts", "triggers"]
        # print the attribs it has
        for v in priority_fields:
            print(f"{v:>35}:", getattr(plugin, v))
        for v in sorted(dir(plugin)):
            if v in priority_fields or v in skip_fields:
                continue
            if v.startswith("_") or inspect.ismethod(getattr(plugin, v)):
                continue
            print(f"{v:>35}:", getattr(plugin, v))

    except ValueError as e:
        print(e)
    except Exception as e:
        print(e)
        print(
            f"Plugin {plugin_name} not found. Try --list_probes, or --list_detectors."
        )


# TODO set config vars - debug, threshold
# TODO load generator
# TODO set probe config string


# do a run
def probewise_run(generator, probe_names, evaluator, buffs):
    import garak.harnesses.probewise

    probewise_h = garak.harnesses.probewise.ProbewiseHarness()
    probewise_h.run(generator, probe_names, evaluator, buffs)


def pxd_run(generator, probe_names, detector_names, evaluator, buffs):
    import garak.harnesses.pxd

    pxd_h = garak.harnesses.pxd.PxD()
    pxd_h.run(
        generator,
        probe_names,
        detector_names,
        evaluator,
        buffs,
    )


def _enumerate_obj_values(o):
    for i in dir(o):
        if i[:2] != "__" and not callable(getattr(o, i)):
            print(f"    {i}: {getattr(o, i)}")


def list_config():
    from garak import _config

    print("_config:")
    _enumerate_obj_values(_config)

    for section in "system transient run plugins".split():
        print(f"{section}:")
        _enumerate_obj_values(getattr(_config, section))
