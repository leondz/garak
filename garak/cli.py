#!/usr/bin/env python3


def main(arguments=[]) -> None:
    def print_plugins(prefix, color):
        from garak._plugins import enumerate_plugins

        plugin_names = enumerate_plugins(category=prefix).values()
        plugin_names = [n.replace(f"{prefix}.", "") for n in plugin_names]
        module_names = set([n.split(".")[0] for n in plugin_names])
        plugin_names += module_names
        for plugin_name in sorted(plugin_names):
            print(f"{Style.BRIGHT}{color}{prefix}: {Style.RESET_ALL}", end="")
            print(plugin_name, end="")
            if "." not in plugin_name:
                print(f" 🌟", end="")
            print()

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
    parser.add_argument(
        "--seed", "-s", type=int, nargs="?", default=320, help="random seed"
    )
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
        "--eval_threshold",
        type=float,
        default=0.5,
        help="minimum threshold for a successful hit",
    )
    parser.add_argument(
        "--plugin_info", "-P", type=str, help="show info about one plugin"
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
        "-V", "--version", action="store_true", help="print version info & exit"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    _config.args = parser.parse_args(arguments)

    import logging

    logging.basicConfig(
        filename="garak.log",
        level=logging.DEBUG,
        format="%(asctime)s  %(levelname)s  %(message)s",
    )

    logging.info(f"invoked with arguments {_config.args}")

    import importlib
    import json

    from colorama import Fore, Style

    import garak.evaluators
    from garak._plugins import enumerate_plugins, load_plugin

    if not _config.args.version:
        logging.info(f"started at {_config.starttime_iso}")
        report_uniqueish_id = abs(hash(dir))
        report_filename = f"garak.{report_uniqueish_id}.jsonl"
        _config.reportfile = open(report_filename, "w", buffering=1)
        _config.reportfile.write(json.dumps(str(_config.args)) + "\n")
        _config.reportfile.write(
            json.dumps(
                {"garak_version": _config.version, "start_time": _config.starttime_iso}
            )
            + "\n"
        )
        logging.info(f"reporting to {report_filename}")

    if _config.args.version:
        pass

    elif _config.args.plugin_info:
        # load plugin
        try:
            plugin = load_plugin(_config.args.plugin_info)
            print(f"Info on {_config.args.plugin_info}:")
            priority_fields = ["name", "description"]
            # print the attribs it has
            for v in priority_fields:
                print(f"{v:>45}:", vars(plugin)[v])
            for v in sorted(vars(plugin)):
                if v in priority_fields:
                    continue
                print(f"{v:>45}:", vars(plugin)[v])

        except:
            print(
                f"Plugin {_config.args.plugin_info} not found. Try --list_probes, or --list_detectors."
            )
    elif _config.args.list_probes:
        print_plugins("probes", Fore.LIGHTYELLOW_EX)

    elif _config.args.list_detectors:
        print_plugins("detectors", Fore.LIGHTBLUE_EX)

    elif _config.args.list_generators:
        print_plugins("generators", Fore.LIGHTMAGENTA_EX)

    elif _config.args.model_type:
        if (
            _config.args.model_type in ("openai", "replicate", "ggml", "huggingface")
            and not _config.args.model_name
        ):
            message = f"⚠️  Model type '{_config.args.model_type}' also needs a model name\n You can set one with e.g. --model_name \"billwurtz/gpt-1.0\""
            logging.error(message)
            raise ValueError(message)
        print(f"📜 reporting to {report_filename}")
        generator_module_name = _config.args.model_type.split(".")[0]
        generator_mod = importlib.import_module(
            "garak.generators." + generator_module_name
        )
        if "." not in _config.args.model_type:
            if generator_mod.default_class:
                generator_class_name = generator_mod.default_class
            else:
                raise Exception(
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

        if _config.args.probes == "all":
            probe_names = enumerate_plugins(category="probes").values()
        else:
            probe_names = []
            for probe_clause in _config.args.probes.split(","):
                if probe_clause.count(".") < 1:
                    probe_names += [
                        p
                        for p in enumerate_plugins(category="probes").values()
                        if p.startswith(f"probes.{probe_clause}.")
                    ]
                else:
                    probe_names += ["probes." + probe_clause]

        evaluator = garak.evaluators.ThresholdEvaluator(_config.args.eval_threshold)

        detector_names = []
        if _config.args.detectors == "":
            pass
        elif _config.args.detectors == "all":
            detector_names = enumerate_plugins(category="detectors").values()
        else:
            detector_clauses = _config.args.detectors.split(",")
            for detector_clause in detector_clauses:
                if detector_clause.count(".") < 1:
                    detector_names += [
                        d
                        for d in enumerate_plugins(category="detectors").values()
                        if d.startswith(f"detectors.{detector_clause}.")
                    ]
                else:
                    detector_names += ["detectors." + detector_clause]

        if detector_names == []:
            import garak.harness.probewise

            h = garak.harness.probewise.ProbewiseHarness()
            h.run(generator, probe_names, evaluator)
        else:
            import garak.harness.pxd

            h = garak.harness.pxd.PxD()
            h.run(generator, probe_names, detector_names, evaluator)

        logging.info("run complete, ending")
        _config.reportfile.close()
        print(f"📜 report closed :) {report_filename}")

        timetaken = (datetime.datetime.now() - _config.starttime).total_seconds()

        print(f"✔️  garak done: complete in {timetaken:.2f}s")
        logging.info(f"garak done: complete in {timetaken:.2f}s")

    else:
        print("nothing to do 🤷  try --help")
        if _config.args.model_name and not _config.args.model_type:
            print(
                "💡 try setting --model_type (--model_name is currently set but not --model_type)"
            )
        logging.info("nothing to do 🤷")
