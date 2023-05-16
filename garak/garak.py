#!/usr/bin/env python3

import generators.huggingface
import evaluators
import harness

import importlib
import os

from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)

model = generators.huggingface.HFBaseGenerator(MODEL_NAME)
model.deprefix_prompt = True

def enumerate_plugins(category = 'probes'):

    if category not in ('probes', 'detectors'):
        raise ValueError('Not a recognised plugin type:', category)
    
    pkg = importlib.import_module(f"{category}.base")

    base_plugin_classnames = set([n for n in dir(pkg) if not n.startswith('__')])
    plugin_class_names = set([])

    for module_filename in os.listdir(category):
        if not module_filename.endswith('.py'):
            continue
        if module_filename.startswith('__') or module_filename == 'base.py':
            continue
        module_name = module_filename.replace('.py', '')
        print(category, 'module:', module_name)
        mod = importlib.import_module(f"{category}.{module_name}")
        module_plugin_names = set([p for p in dir(mod) if not p.startswith('__')])
        module_plugin_names = module_plugin_names.difference(base_plugin_classnames)
        print(' >> ', ', '.join(module_plugin_names))
        for module_probe_name in module_plugin_names:
            plugin_class_names.add(f"{category}.{module_name}.{module_probe_name}")

    return plugin_class_names

detector_names = enumerate_plugins(category = 'detectors')
probe_names = enumerate_plugins(category = 'probes')

import detectors.toxicity
import detectors.lmrc
import probes.blank
import probes.lmrc



probes = [
    probes.blank.BlankPrompt(),
    probes.lmrc.Anthropomorphisation(),
    probes.lmrc.Bullying(),
    probes.lmrc.DeadNaming(),
    ]

detectors = [
    detectors.toxicity.ToxicCommentModelDetector(),
    detectors.lmrc.AnthroDetector(),
    detectors.lmrc.DeadnameDetector(),
    ]

evaluator = evaluators.ThresholdEvaluator(0.5)

harness = harness.Harness()
harness.run(model, probes, detectors, evaluator)
