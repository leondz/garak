#!/usr/bin/env python3

import argparse
import _config

parser = argparse.ArgumentParser(
    description="LLM safety & security scanning tool",
    epilog="See https://github.com/leondz/garak",
)
# model type; model name; seed; generations; probe names; eval threshold
parser.add_argument(
    "--model_type",
    type=str,
    help="class of the generator, e.g. 'huggingface.HFBaseGenerator'",
    required=True,
)
parser.add_argument(
    "--model_name",
    type=str,
    nargs="?",
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
    help="list of probe names to use, or * for all",
)
parser.add_argument(
    "--eval_threshold",
    type=float,
    default=0.5,
    help="minimum threshold for a successful hit",
)
_config.args = parser.parse_args()

import logging

logging.basicConfig(
    filename="garak.log",
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logging.info(f"invoked with arguments {_config.args}")

report_filename = "garak.jsonl"
_config.reportfile = open(report_filename, "w")
logging.info(f"reporting to {report_filename}")

import importlib

import evaluators
import harness
from _plugins import enumerate_plugins

generator_module_name, generator_class_name = _config.args.model_type.split(".")
generator_mod = importlib.import_module("generators." + generator_module_name)
generator = getattr(generator_mod, generator_class_name)(_config.args.model_name)
generator.generations = _config.args.generations

if _config.args.probes == "*":
    probe_names = enumerate_plugins(category="probes").values()
elif len(_config.args.probes[0].split('.')) == 1:
    probe_names = [p for p in enumerate_plugins(category="probes").values() if p.startswith('probes.'+_config.args.probes[0])]
else:
    probe_names = ["probes." + name for name in _config.args.probes]

evaluator = evaluators.ThresholdEvaluator(_config.args.eval_threshold)

harness = harness.ProbewiseHarness()
logging.debug(f"harness run: {harness}")
harness.run(generator, probe_names, evaluator)
logging.info("run complete, ending")
