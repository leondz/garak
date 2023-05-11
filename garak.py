#!/usr/bin/env python3

import generators.huggingface
import probes.blank
import detectors.toxicity
import evaluators
import harness

from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)

model = generators.huggingface.HFBaseGenerator(MODEL_NAME)

probes = [
    probes.blank.BlankPrompt(),
    ]

detectors = [
    detectors.toxicity.ToxicCommentModelDetector(),
    ]

evaluator = evaluators.ThresholdEvaluator(0.5)

harness = harness.Harness()
harness.run(model, probes, detectors, evaluator)
