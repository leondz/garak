#!/usr/bin/env python3

import os

import replicate

import garak._config
from garak.generators.base import Generator

if os.getenv("REPLICATE_API_TOKEN", default=None) == None:
    raise Exception(
        'Put the Replicate API token in the REPLICATE_API_TOKEN environment variable (this was empty)\n \
        e.g.: export REPLICATE_API_TOKEN="r8-123XXXXXXXXXXXX"'
        )



class ReplicateGenerator(Generator):
    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"Replicate {self.name}"
        self.generations = generations

        self.max_length = 200
        self.temperature = 1
        self.top_p = 1.0
        self.repetition_penalty = 1
        self.seed = garak._config.seed

        self.generator_family_name = "Replicate"
        super().__init__(name)


    def generate(self, prompt):
        outputs = []
        for i in range(self.generations):
            response_iterator = replicate.run(
                self.name,
                input={
                    "prompt": prompt,
                    "max_length": self.max_length,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "repetition_penalty": self.repetition_penalty,
                    "seed": self.seed,
                },
            )
            outputs.append("".join(response_iterator))
        return outputs


default_class = "ReplicateGenerator"
