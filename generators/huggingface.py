#!/usr/bin/env python3

from transformers import pipeline

class HFBaseGenerator:
    def __init__(self, name, do_sample=True, num_return_sequences=10):
        self.generator = pipeline(
            'text-generation', 
            model=name, 
            do_sample=do_sample,
            num_return_sequences=num_return_sequences)

    def generate(self, prompt):
        raw_output = self.generator(prompt)
        return [i['generated_text'] for i in raw_output]
