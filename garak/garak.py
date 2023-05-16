#!/usr/bin/env python3

import generators.huggingface
import evaluators
import harness
from _plugins import enumerate_plugins, load_plugin

from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)


"""
detector_names = enumerate_plugins(category = 'detectors')
detectors = [load_plugin(detector_name) for detector_name in detector_names.values()]

probe_names = enumerate_plugins(category = 'probes')

import probes.dan

probes = [
    probes.dan.ChatGPT_Image_Markdown()
    ]


harness = harness.Harness()
harness.run(model, probes, detectors, evaluator)
"""

probe_names = enumerate_plugins(category = 'probes').values()

evaluator = evaluators.ThresholdEvaluator(0.5)

model = generators.huggingface.HFBaseGenerator(MODEL_NAME)
model.deprefix_prompt = True

harness = harness.ProbewiseHarness()
harness.run(model, probe_names, evaluator)