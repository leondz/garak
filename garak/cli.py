#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Flow for invoking garak from the command line"""


def main(arguments=[]) -> None:
    import datetime

    from garak import __version__, __description__, _config

    _config.starttime = datetime.datetime.now()
    _config.starttime_iso = _config.starttime.isoformat()
    _config.version = __version__

    print(
        f"garak {__description__} v{_config.version} ( https://github.com/leondz/garak ) at {_config.starttime_iso}"
    )

    import argparse

    parser = argparse.ArgumentParser(
        description="LLM safety & security scanning tool",
        epilog="See https://github.com/leondz/garak",
    )
    # model type; model name; seed; generations; probe names; eval threshold
    parser.add_argument(
        "--model_type",
        "-m",
        type=str,
        help="module and optionally also class of the generator, e.g. 'huggingface', or 'openai'",
    )
    parser.add_argument(
        "--model_name",
        "-n",
        type=str,
        default=None,
        help="name of the model, e.g. 'timdettmers/guanaco-33b-merged'",
    )
    parser.add_argument("--seed", "-s", type=int, default=None, help="random seed")
    parser.add_argument(
        "--generations",
        "-g",
        type=int,
        default=10,
        help="number of generations per prompt",
    )
    parser.add_argument(
        "--probes",
        "-p",
        type=str,
        default="all",
        help="list of probe names to use, or 'all' for all (default).",
    )
    parser.add_argument(
        "--detectors",
        "-d",
        type=str,
        default="",
        help="list of detectors to use, or 'all' for all. Default is to use the probe's suggestion.",
    )
    parser.add_argument(
        "--buff",
        "-b",
        type=str,
        default="",
        help="buff to use",
    )
    parser.add_argument(
        "--eval_threshold",
        type=float,
        default=0.5,
        help="minimum threshold for a successful hit",
    )
    parser.add_argument(
        "--deprefix",
        action="store_false",
        help="remove the prompt from the front of system output",
    )
    parser.add_argument(
        "--plugin_info",
        type=str,
        help="show info about one plugin; format as type.plugin.class, e.g. probes.lmrc.Profanity",
    )
    parser.add_argument(
        "--list_probes", action="store_true", help="list available vulnerability probes"
    )
    parser.add_argument(
        "--list_detectors", action="store_true", help="list available detectors"
    )
    parser.add_argument(
        "--list_generators",
        action="store_true",
        help="list available generation model interfaces",
    )
    parser.add_argument(
        "--list_buffs",
        action="store_true",
        help="list available buffs/fuzzes",
    )
    parser.add_argument(
        "--version", "-V", action="store_true", help="print version info & exit"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="add one or more times to increase verbosity of output during runtime",
    )
    generator_args = parser.add_mutually_exclusive_group()
    generator_args.add_argument(
        "--generator_option_file",
        "-G",
        type=str,
        help="path to JSON file containing options to pass to generator",
    )
    generator_args.add_argument(
        "--generator_options",
        type=str,
        help="options to pass to the generator",
    )
    probe_args = parser.add_mutually_exclusive_group()
    probe_args.add_argument(
        "--probe_option_file",
        "-P",
        type=str,
        help="path to JSON file containing options to pass to probes",
    )
    probe_args.add_argument(
        "--probe_options",
        type=str,
        help="options to pass to probes, formatted as a JSON dict",
    )
    parser.add_argument(
        "--report_prefix",
        type=str,
        default="",
        help="Specify an optional prefix for the report and hit logs",
    )
    parser.add_argument(
        "--narrow_output",
        action="store_true",
        help="give narrow CLI output",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        help="process garak report into a list of AVID reports",
    )
    parser.add_argument(
        "--extended_detectors",
        action="store_true",
        help="If detectors aren't specified on the command line, should we run all detectors? (default is just the primary detector, if given, else everything)",
    )
    parser.add_argument(
        "--parallel_requests",
        type=int,
        default=False,
        help="How many generator requests to launch in parallel for a given prompt. Ignored for models that support multiple generations per call.",
    )
    parser.add_argument(
        "--parallel_attempts",
        type=int,
        default=False,
        help="How many probe attempts to launch in parallel.",
    )

    _config.args = parser.parse_args(arguments)

    import garak.command as command

    import logging

    command.start_logging()

    import importlib
    import json

    import garak.evaluators  # why is this line so high up? maybe eval/plugin too tightly coupled?
    from garak._plugins import enumerate_plugins

    if _config.args.version:
        pass

    elif _config.args.plugin_info:
        command.plugin_info(_config.args.plugin_info)

    elif _config.args.list_probes:
        command.print_probes()

    elif _config.args.list_detectors:
        command.print_detectors()

    elif _config.args.list_buffs:
        command.print_buffs()

    elif _config.args.list_generators:
        command.print_generators()

    elif _config.args.report:
        from garak.report import Report

        report_location = _config.args.report
        print(f"📜 Converting garak reports {report_location}")
        report = Report(_config.args.report).load().get_evaluations()
        report.export()
        print(f"📜 AVID reports generated at {report.write_location}")

    elif _config.args.model_type:  # model is specified, we're doing something
        command.start_run()

        if _config.args.probe_option_file or _config.args.probe_options:
            if _config.args.probe_option_file:
                with open(_config.args.probe_option_file, encoding="utf-8") as f:
                    probe_options_json = f.read().strip()
            elif _config.args.probe_options:
                probe_options_json = _config.args.probe_options
            try:
                _config.probe_options = json.loads(probe_options_json)
            except json.decoder.JSONDecodeError as e:
                logging.warning("Failed to parse JSON probe_options: %s", {e.args[0]})
                raise e

        if _config.args.generator_option_file or _config.args.generator_options:
            if _config.args.generator_option_file:
                with open(_config.args.generator_option_file, encoding="utf-8") as f:
                    generator_options_json = f.read().strip()
            elif _config.args.generator_options:
                generator_options_json = _config.args.generator_options
            try:
                _config.generator_options = json.loads(generator_options_json)
            except json.decoder.JSONDecodeError as e:
                logging.warning(
                    "Failed to parse JSON generator_options: %s", {e.args[0]}
                )
                raise e

        if (
            _config.args.model_type in ("openai", "replicate", "ggml", "huggingface")
            and not _config.args.model_name
        ):
            message = f"⚠️  Model type '{_config.args.model_type}' also needs a model name\n You can set one with e.g. --model_name \"billwurtz/gpt-1.0\""
            logging.error(message)
            raise ValueError(message)
        print(f"📜 reporting to {_config.report_filename}")
        generator_module_name = _config.args.model_type.split(".")[0]
        generator_mod = importlib.import_module(
            "garak.generators." + generator_module_name
        )
        if "." not in _config.args.model_type:
            if generator_mod.default_class:
                generator_class_name = generator_mod.default_class
            else:
                raise ValueError(
                    "module {generator_module_name} has no default class; pass module.ClassName to --model_type"
                )
        else:
            generator_class_name = _config.args.model_type.split(".")[1]

        if not _config.args.model_name:
            generator = getattr(generator_mod, generator_class_name)()
        else:
            generator = getattr(generator_mod, generator_class_name)(
                _config.args.model_name
            )
        generator.generations = _config.args.generations
        generator.seed = _config.args.seed

        if _config.args.probes == "all":
            probe_names = [
                name
                for name, active in enumerate_plugins(category="probes")
                if active == True
            ]
        else:
            probe_names = []
            for probe_clause in _config.args.probes.split(","):
                if probe_clause.count(".") < 1:
                    probe_names += [
                        p
                        for p, a in enumerate_plugins(category="probes")
                        if p.startswith(f"probes.{probe_clause}.") and a == True
                    ]
                else:
                    probe_names += ["probes." + probe_clause]

        evaluator = garak.evaluators.ThresholdEvaluator(_config.args.eval_threshold)

        detector_names = []
        if _config.args.detectors == "" or _config.args.detectors == "auto":
            pass
        elif _config.args.detectors == "all":
            detector_names = [
                name
                for name, active in enumerate_plugins(category="detectors")
                if active == True
            ]
        else:
            detector_clauses = _config.args.detectors.split(",")
            for detector_clause in detector_clauses:
                if detector_clause.count(".") < 1:
                    detector_names += [
                        d
                        for d, a in enumerate_plugins(category="detectors")
                        if d.startswith(f"detectors.{detector_clause}.") and a == True
                    ]
                else:
                    detector_names += ["detectors." + detector_clause]

        if _config.args.buff:
            buffs = [_config.args.buff]
        else:
            buffs = []

        if detector_names == []:
            command.probewise_run(generator, probe_names, evaluator, buffs)

        else:
            command.pxd_run(generator, probe_names, detector_names, evaluator, buffs)

        command.end_run()

    else:
        print("nothing to do 🤷  try --help")
        if _config.args.model_name and not _config.args.model_type:
            print(
                "💡 try setting --model_type (--model_name is currently set but not --model_type)"
            )
        logging.info("nothing to do 🤷")
