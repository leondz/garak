#!/usr/bin/env python3

import generators.huggingface
import detectors.toxicity
import detectors.lmrc
import probes.blank
import probes.lmrc
import evaluators
import harness

from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)

model = generators.huggingface.HFBaseGenerator(MODEL_NAME)
model.deprefix_prompt = True

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
