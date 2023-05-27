#!/usr/bin/env python3


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
        type=str,
        help="module and optionally also class of the generator, e.g. 'huggingface.HFBaseGenerator', or 'openai'",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="",
        help="name of the model, e.g. 'gpt2'",
    )
    parser.add_argument("--seed", type=int, nargs="?", default=320, help="random seed")
    parser.add_argument(
        "--generations", type=int, default=10, help="number of generations per prompt"
    )
    parser.add_argument(
        "--probes",
        type=str,
        nargs="*",
        default="*",
        help="list of probe names to use, or * for all (default)",
    )
    parser.add_argument(
        "--eval_threshold",
        type=float,
        default=0.5,
        help="minimum threshold for a successful hit",
    )
    parser.add_argument("--list_probes", action="store_true")
    parser.add_argument("--list_detectors", action="store_true")
    parser.add_argument("--list_generators", action="store_true")
    parser.add_argument("--version", action="store_true")
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

    import garak.evaluators
    import garak.harness.probewise
    from garak._plugins import enumerate_plugins

    if not _config.args.version:
        logging.info(f"started at {_config.starttime_iso}")
        report_uniqueish_id = abs(hash(dir))
        report_filename = f"garak.{report_uniqueish_id}.jsonl"
        _config.reportfile = open(report_filename, "w", buffering=1)
        _config.reportfile.write(json.dumps(str(_config.args)) + "\n")
        logging.info(f"reporting to {report_filename}")

    if _config.args.version:
        pass

    elif _config.args.list_probes:
        probe_names = enumerate_plugins(category="probes").values()
        print("\n".join(probe_names))

    elif _config.args.list_detectors:
        probe_names = enumerate_plugins(category="detectors").values()
        print("\n".join(probe_names))

    elif _config.args.list_generators:
        probe_names = enumerate_plugins(category="generators").values()
        print("\n".join(probe_names))

    elif _config.args.model_type:
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
        generator = getattr(generator_mod, generator_class_name)(
            _config.args.model_name
        )
        generator.generations = _config.args.generations

        if _config.args.probes == "*":
            probe_names = enumerate_plugins(category="probes").values()
        elif len(_config.args.probes[0].split(".")) == 1:
            probe_names = [
                p
                for p in enumerate_plugins(category="probes").values()
                if p.startswith("probes." + _config.args.probes[0])
            ]
        else:
            probe_names = ["probes." + name for name in _config.args.probes]

        evaluator = garak.evaluators.ThresholdEvaluator(_config.args.eval_threshold)

        h = garak.harness.probewise.ProbewiseHarness()
        logging.debug(f"harness run: {h}")
        h.run(generator, probe_names, evaluator)
        logging.info("run complete, ending")
        _config.reportfile.close()
        print(f"📜 report log closed :) {report_filename}")

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
