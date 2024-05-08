# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Flow for invoking garak from the command line"""

command_options = "list_detectors list_probes list_generators list_buffs list_config plugin_info interactive report version".split()


def main(arguments=[]) -> None:
    """Main entry point for garak runs invoked from the CLI"""
    import datetime

    from garak import __version__, __description__
    from garak import _config

    _config.transient.starttime = datetime.datetime.now()
    _config.transient.starttime_iso = _config.transient.starttime.isoformat()
    _config.version = __version__

    import garak.command as command
    import logging
    import re

    command.start_logging()
    _config.load_base_config()

    print(
        f"garak {__description__} v{_config.version} ( https://github.com/leondz/garak ) at {_config.transient.starttime_iso}"
    )

    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m garak",
        description="LLM safety & security scanning tool",
        epilog="See https://github.com/leondz/garak",
    )

    ## SYSTEM
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=_config.system.verbose,
        help="add one or more times to increase verbosity of output during runtime",
    )
    parser.add_argument(
        "--report_prefix",
        type=str,
        default=_config.reporting.report_prefix,
        help="Specify an optional prefix for the report and hit logs",
    )
    parser.add_argument(
        "--narrow_output",
        action="store_true",
        help="give narrow CLI output",
    )
    parser.add_argument(
        "--parallel_requests",
        type=int,
        default=_config.system.parallel_requests,
        help="How many generator requests to launch in parallel for a given prompt. Ignored for models that support multiple generations per call.",
    )
    parser.add_argument(
        "--parallel_attempts",
        type=int,
        default=_config.system.parallel_attempts,
        help="How many probe attempts to launch in parallel.",
    )

    ## RUN
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=_config.run.seed,
        help="random seed",
    )
    parser.add_argument(
        "--deprefix",
        action="store_false",
        help="remove the prompt from the front of generator output",
    )
    parser.add_argument(
        "--eval_threshold",
        type=float,
        default=_config.run.eval_threshold,
        help="minimum threshold for a successful hit",
    )
    parser.add_argument(
        "--generations",
        "-g",
        type=int,
        default=_config.run.generations,
        help="number of generations per prompt",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="YAML config file for this run"
    )

    ## PLUGINS
    # generator
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
    # probes
    parser.add_argument(
        "--probes",
        "-p",
        type=str,
        default=_config.plugins.probe_spec,
        help="list of probe names to use, or 'all' for all (default).",
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
    probe_args.add_argument(
        "--probe_tags",
        default=_config.run.probe_tags,
        type=str,
        help="only include probes with a tag that starts with this value (e.g. owasp:llm01)",
    )
    # detectors
    parser.add_argument(
        "--detectors",
        "-d",
        type=str,
        default=_config.plugins.detector_spec,
        help="list of detectors to use, or 'all' for all. Default is to use the probe's suggestion.",
    )
    parser.add_argument(
        "--extended_detectors",
        action="store_true",
        help="If detectors aren't specified on the command line, should we run all detectors? (default is just the primary detector, if given, else everything)",
    )
    # buffs
    parser.add_argument(
        "--buffs",
        "-b",
        type=str,
        default=_config.plugins.buff_spec,
        help="list of buffs to use. Default is none",
    )

    ## REPORTING
    parser.add_argument(
        "--taxonomy",
        type=str,
        default=_config.reporting.taxonomy,
        help="specify a MISP top-level taxonomy to be used for grouping probes in reporting. e.g. 'avid-effect', 'owasp' ",
    )

    ## COMMANDS
    # items placed here also need to be listed in command_options below
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
        "--list_config",
        action="store_true",
        help="print active config info (and don't scan)",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="print version info & exit",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        help="process garak report into a list of AVID reports",
    )
    parser.add_argument(
        "--interactive",
        "-I",
        action="store_true",
        help="Enter interactive probing mode",
    )
    parser.add_argument(
        "--generate_autodan",
        action="store_true",
        help="generate AutoDAN prompts; requires --prompt_options with JSON containing a prompt and target",
    )
    parser.add_argument(
        "--interactive.py",
        action="store_true",
        help="Launch garak in interactive.py mode",
    )

    logging.debug("args - raw argument string received: %s", arguments)

    args = parser.parse_args(arguments)
    logging.debug("args - full argparse: %s", args)

    # load site config before loading CLI config
    _config.load_config(run_config_filename=args.config)

    # extract what was actually passed on CLI; use a masking argparser
    aux_parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    # print('VARS', vars(args))
    # aux_parser is going to get sys.argv and so also needs the argument shortnames
    # will extract those from parser internals and use them to populate aux_parser
    arg_names = {}
    for action in parser._actions:
        raw_option_strings = [
            re.sub("^" + re.escape(parser.prefix_chars) + "+", "", a)
            for a in action.option_strings
        ]
        if "help" not in raw_option_strings:
            for raw_option_string in raw_option_strings:
                arg_names[raw_option_string] = action.option_strings

    for arg, val in vars(args).items():
        if arg == "verbose":
            # the 'verbose' flag is currently unique and retrieved from `args` directly
            continue
        if isinstance(val, bool):
            if val:
                aux_parser.add_argument(*arg_names[arg], action="store_true")
            else:
                aux_parser.add_argument(*arg_names[arg], action="store_false")
        else:
            aux_parser.add_argument(*arg_names[arg], type=type(val))

    # cli_args contains items specified on CLI; the rest not to be overridden
    cli_args, _ = aux_parser.parse_known_args(arguments)

    # exception: action=count. only verbose uses this, let's bubble it through
    cli_args.verbose = args.verbose

    # print('ARGS', args)
    # print('CLI_ARGS', cli_args)

    # also force command vars through to cli_args, even if false, to make command code easier
    for command_option in command_options:
        setattr(cli_args, command_option, getattr(args, command_option))

    logging.debug("args - cli_args&commands stored: %s", cli_args)

    del args
    args = cli_args
    # stash cli_args
    _config.transient.cli_args = cli_args

    # save args info into config
    # need to know their type: plugin, system, or run
    # ignore params not listed here
    # - sorry, this means duping stuff, i know. maybe better argparse setup will help
    ignored_params = []
    for param, value in vars(args).items():
        if param in _config.system_params:
            setattr(_config.system, param, value)
        elif param in _config.run_params:
            setattr(_config.run, param, value)
        elif param in _config.plugins_params:
            setattr(_config.plugins, param, value)
        elif param in _config.reporting_params:
            setattr(_config.reporting, param, value)
        else:
            ignored_params.append((param, value))
    logging.debug("non-config params: %s", ignored_params)

    # put plugin spec into the _spec config value, if set at cli
    if "probes" in args:
        _config.plugins.probe_spec = args.probes
    if "detectors" in args:
        _config.plugins.detector_spec = args.detectors
    if "buffs" in args:
        _config.plugins.buff_spec = args.buffs

    # startup
    import sys
    import importlib
    import json

    import garak.evaluators

    try:
        if not args.version and not args.report:
            command.start_run()

        # do a special thing for CLIprobe options, generator options
        if "probe_options" in args or "probe_option_file" in args:
            if "probe_options" in args:
                try:
                    probe_cli_config = json.loads(args.probe_options)
                except json.JSONDecodeError as e:
                    logging.warning("Failed to parse JSON probe_options: %s", e.args[0])

            elif "probe_option_file" in args:
                with open(args.probe_option_file, encoding="utf-8") as f:
                    probe_options_json = f.read().strip()
                try:
                    probe_cli_config = json.loads(probe_options_json)
                except json.decoder.JSONDecodeError as e:
                    logging.warning(
                        "Failed to parse JSON probe_options: %s", {e.args[0]}
                    )
                    raise e

            _config.plugins.probes = _config._combine_into(
                probe_cli_config, _config.plugins.probes
            )

        if "generator_options" in args or "generator_option_file" in args:
            if "generator_options" in args:
                try:
                    generator_cli_config = json.loads(args.generator_options)
                except json.JSONDecodeError as e:
                    logging.warning(
                        "Failed to parse JSON generator_options: %s", e.args[0]
                    )

            elif "generator_option_file" in args:
                with open(args.generator_option_file, encoding="utf-8") as f:
                    generator_options_json = f.read().strip()
                try:
                    generator_cli_config = json.loads(generator_options_json)
                except json.decoder.JSONDecodeError as e:
                    logging.warning(
                        "Failed to parse JSON generator_options: %s", {e.args[0]}
                    )
                    raise e

            _config.plugins.generators = _config._combine_into(
                generator_cli_config, _config.plugins.generators
            )

        # process commands
        if args.interactive:
            from garak.interactive import interactive_mode

            try:
                interactive_mode()
            except Exception as e:
                logging.error(e)
                print(e)
                sys.exit(1)

        if args.version:
            pass

        elif args.plugin_info:
            command.plugin_info(args.plugin_info)

        elif args.list_probes:
            command.print_probes()

        elif args.list_detectors:
            command.print_detectors()

        elif args.list_buffs:
            command.print_buffs()

        elif args.list_generators:
            command.print_generators()

        elif args.list_config:
            print("cli args:\n ", args)
            command.list_config()

        elif args.report:
            from garak.report import Report

            report_location = args.report
            print(f"📜 Converting garak reports {report_location}")
            report = Report(args.report).load().get_evaluations()
            report.export()
            print(f"📜 AVID reports generated at {report.write_location}")

        # model is specified, we're doing something
        elif _config.plugins.model_type:
            if (
                _config.plugins.model_type
                in ("openai", "replicate", "ggml", "huggingface", "litellm")
                and not _config.plugins.model_name
            ):
                message = f"⚠️  Model type '{_config.plugins.model_type}' also needs a model name\n You can set one with e.g. --model_name \"billwurtz/gpt-1.0\""
                logging.error(message)
                raise ValueError(message)
            print(f"📜 reporting to {_config.transient.report_filename}")

            generator_module_name = _config.plugins.model_type.split(".")[0]
            generator_mod = importlib.import_module(
                "garak.generators." + generator_module_name
            )
            if "." not in _config.plugins.model_type:
                if generator_mod.default_class:
                    generator_class_name = generator_mod.default_class
                else:
                    raise ValueError(
                        "module {generator_module_name} has no default class; pass module.ClassName to --model_type"
                    )
            else:
                generator_class_name = _config.plugins.model_type.split(".")[1]

            #        if 'model_name' not in args:
            #            generator = getattr(generator_mod, generator_class_name)()
            #        else:
            generator = getattr(generator_mod, generator_class_name)(
                _config.plugins.model_name
            )
            if (
                hasattr(_config.run, "generations")
                and _config.run.generations is not None
            ):
                generator.generations = _config.run.generations
            if hasattr(_config.run, "seed") and _config.run.seed is not None:
                generator.seed = _config.run.seed

            if "generate_autodan" in args and args.generate_autodan:
                from garak.resources.autodan import autodan_generate

                try:
                    prompt = _config.probe_options["prompt"]
                    target = _config.probe_options["target"]
                except Exception as e:
                    print(
                        "AutoDAN generation requires --probe_options with a .json containing a `prompt` and `target` "
                        "string"
                    )
                autodan_generate(generator=generator, prompt=prompt, target=target)

            probe_names = _config.parse_plugin_spec(
                _config.plugins.probe_spec, "probes", _config.run.probe_tags
            )
            detector_names = _config.parse_plugin_spec(
                _config.plugins.detector_spec, "detectors"
            )
            buff_names = _config.parse_plugin_spec(_config.plugins.buff_spec, "buffs")

            evaluator = garak.evaluators.ThresholdEvaluator(_config.run.eval_threshold)

            if detector_names == []:
                command.probewise_run(generator, probe_names, evaluator, buff_names)

            else:
                command.pxd_run(
                    generator, probe_names, detector_names, evaluator, buff_names
                )

            command.end_run()
        else:
            print("nothing to do 🤷  try --help")
            if _config.plugins.model_name and not _config.plugins.model_type:
                print(
                    "💡 try setting --model_type (--model_name is currently set but not --model_type)"
                )
            logging.info("nothing to do 🤷")
    except KeyboardInterrupt:
        print("User cancel received, terminating all runs")
