#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Definitions of commands and actions that can be run in the garak toolkit"""

import json


def start_logging():
    import logging

    import garak._config as _config

    logging.basicConfig(
        filename="garak.log",
        level=logging.DEBUG,
        format="%(asctime)s  %(levelname)s  %(message)s",
    )

    logging.info(f"invoked with arguments {_config.args}")


def start_run():
    import logging
    import uuid

    import garak._config as _config

    logging.info(f"started at {_config.starttime_iso}")
    _config.run_id = str(uuid.uuid4())  # uuid1 is safe but leaks host info
    if not _config.args.report_prefix:
        _config.report_filename = f"garak.{_config.run_id}.report.jsonl"
    else:
        _config.report_filename = _config.args.report_prefix + ".report.jsonl"
    _config.reportfile = open(_config.report_filename, "w", buffering=1)
    _config.args.__dict__.update({"entry_type": "config"})
    _config.reportfile.write(json.dumps(_config.args.__dict__) + "\n")
    _config.reportfile.write(
        json.dumps(
            {
                "entry_type": "init",
                "garak_version": _config.version,
                "start_time": _config.starttime_iso,
                "run": _config.run_id,
            }
        )
        + "\n"
    )
    logging.info(f"reporting to {_config.report_filename}")


def end_run():
    import datetime
    import logging

    import garak._config as _config

    logging.info("run complete, ending")
    _config.reportfile.close()
    print(f"📜 report closed :) {_config.report_filename}")
    if _config.hitlogfile:
        _config.hitlogfile.close()

    timetaken = (datetime.datetime.now() - _config.starttime).total_seconds()

    print(f"✔️  garak done: complete in {timetaken:.2f}s")
    logging.info(f"garak done: complete in {timetaken:.2f}s")


def print_plugins(prefix: str, color):
    from colorama import Fore, Style

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

    import garak._config as _config
    from garak._plugins import enumerate_plugins, load_plugin

    # load plugin
    try:
        plugin = load_plugin(plugin_name)
        print(f"Info on {plugin_name}:")
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


# set config vars - debug, threshold
# load generator
# probe


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
