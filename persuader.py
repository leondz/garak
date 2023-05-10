#!/usr/bin/env python3

import generators.huggingface
import probes.blank
import detectors.toxicity
from transformers import set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "gpt2"

set_seed(SEED)

model = generators.huggingface.HFBaseGenerator("gpt2")

b = probes.blank.BlankPrompt()

results = b.probe(model)

t = detectors.toxicity.ToxicCommentModelDetector()

print(list(t.detect(results)))