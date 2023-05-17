#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(
    description="LLM safety & security scanning tool",
    epilog="See https://github.com/leondz/garak"
    )
# model type; model name; seed; generations; probe names; eval threshold
parser.add_argument('--model_type', type=str, help="class of the generator, e.g. 'huggingface.HFBaseGenerator'", required=True)
parser.add_argument('--model_name', type=str, nargs='?', help="name of the model, e.g. 'gpt2'")
parser.add_argument('--seed', type=int, nargs="?", default=320, help="random seed")
parser.add_argument('--generations', type=int, default=10, help="number of generations per prompt")
parser.add_argument('--probes', type=str, nargs="*", default="*", help='list of probe names to use, or * for all')
parser.add_argument('--eval_threshold', type=float, default=0.5, help="minimum threshold for a successful hit")
args = parser.parse_args()
print(args)

import importlib

from transformers import set_seed

import evaluators
import harness
from _plugins import enumerate_plugins


generator_module_name, generator_class_name = args.model_type.split('.')
generator_mod = importlib.import_module('generators.' + generator_module_name)

if not args.model_name:
    model = getattr(generator_mod, generator_class_name)()
else:
    model = getattr(generator_mod, generator_class_name)(args.model_name)

model.deprefix_prompt = True

GENERATIONS_PER_ATTEMPT = 10

set_seed(args.seed)

if args.probes == "*":
    probe_names = enumerate_plugins(category = 'probes').values()
else:
    probe_names = ['probes.'+name for name in args.probes]

evaluator = evaluators.ThresholdEvaluator(0.5)


harness = harness.ProbewiseHarness()
harness.run(model, probe_names, evaluator)