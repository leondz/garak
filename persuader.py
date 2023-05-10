#!/usr/bin/env python3

import generators.huggingface
import probes.blank
import detectors.toxicity
import evaluators.base
from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)

model = generators.huggingface.HFBaseGenerator("gpt2")

b = probes.blank.BlankPrompt()

generations = b.probe(model)

t = detectors.toxicity.ToxicCommentModelDetector()

e = evaluators.base.ThresholdEvaluator(0.5)

results = t.detect(generations)

e.evaluate({t.name:results})