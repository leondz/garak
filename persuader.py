#!/usr/bin/env python3

from transformers import pipeline, set_seed

GENERATIONS_PER_ATTEMPT = 10
SEED = 320
MODEL_NAME = "facebook/opt-1.3b"

set_seed(320)
generator = pipeline(
    'text-generation', 
    model=MODEL_NAME, 
    do_sample=True, 
    num_return_sequences=GENERATIONS_PER_ATTEMPT)

output = generator('', )

t = modules.realtoxicityprompts.ToxicCommentModelDetector()

print(list(t.detect(output))