# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Flow for invoking garak from the command line"""

command_options = "list_detectors list_probes list_generators list_buffs list_config plugin_info interactive report version".split()


def main(arguments=None) -> None:
    """Main entry point for garak runs invoked from the CLI"""
    import datetime

    from garak import __version__, __description__
    from garak import _config
    from garak.exception import GarakException

    _config.transient.starttime = datetime.datetime.now()
    _config.transient.starttime_iso = _config.transient.starttime.isoformat()
    _config.version = __version__

    if arguments is None:
        arguments = []

    import garak.command as command
    import logging
    import re
    from colorama import Fore, Style

    log_filename = command.start_logging()
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
    parser.add_argument(
        "--skip_unknown",
        action="store_true",
        help="allow skip of unknown probes, detectors, or buffs",
    )
    parser.add_argument(
        "--proxies",
        type=str,
        help="allow proxy settings for rest generator",
    )
    parser.add_argument(
        "--verify_ssl",
        type=str,
        help="expose SSL verification settings for rest generator",
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
    token_refresh_args = parser.add_mutually_exclusive_group()
    token_refresh_args.add_argument(
        "--token_refresh_config",
        type=str,
        help="path to JSON file containing configuration for the request that fetches a new token",
    )
    # probes
    parser.add_argument(
        "--probes",
        "-p",
        type=str,
        default=_config.plugins.probe_spec,
        help="list of probe names to use, or 'all' for all (default).",
    )
    parser.add_argument(
        "--probe_tags",
        default=_config.run.probe_tags,
        type=str,
        help="only include probes with a tag that starts with this value (e.g. owasp:llm01)",
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
    import json
    import os

    import garak.evaluators

    try:
        plugin_types = ["probe", "generator"]
        # do a special thing for CLI probe options, generator options
        for plugin_type in plugin_types:
            opts_arg = f"{plugin_type}_options"
            opts_file = f"{plugin_type}_option_file"
            if opts_arg in args or opts_file in args:
                if opts_arg in args:
                    opts_argv = getattr(args, opts_arg)
                    try:
                        opts_cli_config = json.loads(opts_argv)
                    except json.JSONDecodeError as e:
                        logging.warning(
                            "Failed to parse JSON %s: %s", opts_arg, e.args[0]
                        )

                elif opts_file in args:
                    file_arg = getattr(args, opts_file)
                    if not os.path.isfile(file_arg):
                        raise FileNotFoundError(
                            f"Path provided is not a file: {opts_file}"
                        )
                    with open(file_arg, encoding="utf-8") as f:
                        options_json = f.read().strip()
                    try:
                        opts_cli_config = json.loads(options_json)
                    except json.decoder.JSONDecodeError as e:
                        logging.warning(
                            "Failed to parse JSON %s: %s", opts_file, {e.args[0]}
                        )
                        raise e

                config_plugin_type = getattr(_config.plugins, f"{plugin_type}s")

                config_plugin_type = _config._combine_into(
                    opts_cli_config, config_plugin_type
                )

        # process commands
        if args.interactive:
            from garak.interactive import interactive_mode

            try:
                command.start_run()  # start run to track actions
                interactive_mode()
            except Exception as e:
                logging.error(e)
                print(e)
                sys.exit(1)
            finally:
                command.end_run()

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

            print(f"📜 logging to {log_filename}")

            conf_root = _config.plugins.generators
            for part in _config.plugins.model_type.split("."):
                if not part in conf_root:
                    conf_root[part] = {}
                conf_root = conf_root[part]
            if _config.plugins.model_name:
                # if passed generator options and config files are already loaded
                # cli provided name overrides config from file
                conf_root["name"] = _config.plugins.model_name
            if hasattr(_config.run, "seed") and _config.run.seed is not None:
                conf_root["seed"] = _config.run.seed

            # Can this check be deferred to the generator instantiation?
            if (
                _config.plugins.model_type
                in ("openai", "replicate", "ggml", "huggingface", "litellm")
                and not _config.plugins.model_name
            ):
                message = f"⚠️  Model type '{_config.plugins.model_type}' also needs a model name\n You can set one with e.g. --model_name \"billwurtz/gpt-1.0\""
                logging.error(message)
                raise ValueError(message)

            parsable_specs = ["probe", "detector", "buff"]
            parsed_specs = {}
            for spec_type in parsable_specs:
                spec_namespace = f"{spec_type}s"
                config_spec = getattr(_config.plugins, f"{spec_type}_spec", "")
                config_tags = getattr(_config.run, f"{spec_type}_tags", "")
                names, rejected = _config.parse_plugin_spec(
                    config_spec, spec_namespace, config_tags
                )
                parsed_specs[spec_type] = names
                if rejected is not None and len(rejected) > 0:
                    if hasattr(args, "skip_unknown"):  # attribute only set when True
                        header = f"Unknown {spec_namespace}:"
                        skip_msg = Fore.LIGHTYELLOW_EX + "SKIP" + Style.RESET_ALL
                        msg = f"{Fore.LIGHTYELLOW_EX}{header}\n" + "\n".join(
                            [f"{skip_msg} {spec}" for spec in rejected]
                        )
                        logging.warning(f"{header} " + ",".join(rejected))
                        print(msg)
                    else:
                        msg_list = ",".join(rejected)
                        raise ValueError(f"❌Unknown {spec_namespace}❌: {msg_list}")

            for probe in parsed_specs["probe"]:
                # distribute `generations` to the probes
                p_type, p_module, p_klass = probe.split(".")
                if (
                    hasattr(_config.run, "generations")
                    and _config.run.generations
                    is not None  # garak.core.yaml always provides run.generations
                ):
                    _config.plugins.probes[p_module][p_klass][
                        "generations"
                    ] = _config.run.generations

            evaluator = garak.evaluators.ThresholdEvaluator(_config.run.eval_threshold)

            from garak import _plugins

            generator = _plugins.load_plugin(
                f"generators.{_config.plugins.model_type}", config_root=_config
            )

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

            command.start_run()  # start the run now that all config validation is complete
            print(f"📜 reporting to {_config.transient.report_filename}")

            if parsed_specs["detector"] == []:
                command.probewise_run(
                    generator, parsed_specs["probe"], evaluator, parsed_specs["buff"]
                )
            else:
                command.pxd_run(
                    generator,
                    parsed_specs["probe"],
                    parsed_specs["detector"],
                    evaluator,
                    parsed_specs["buff"],
                )

            command.end_run()
        else:
            print("nothing to do 🤷  try --help")
            if _config.plugins.model_name and not _config.plugins.model_type:
                print(
                    "💡 try setting --model_type (--model_name is currently set but not --model_type)"
                )
            logging.info("nothing to do 🤷")
    except KeyboardInterrupt as e:
        msg = "User cancel received, terminating all runs"
        logging.exception(e)
        logging.info(msg)
        print(msg)
    except (ValueError, GarakException) as e:
        logging.exception(e)
        print(e)
