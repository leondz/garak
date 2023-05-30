#!/usr/bin/env python3

import logging
import os

import cohere


from garak.generators.base import Generator

api_key = os.getenv("COHERE_API_KEY", default=None)
if api_key == None:
    raise Exception(
        'Put the Cohere API key in the COHERE_API_KEY environment variable (this was empty)\n \
        e.g.: export COHERE_API_KEY="XXXXXXX"'
    )

COHERE_GENERATION_LIMIT = (
    5  # c.f. https://docs.cohere.com/reference/generate 18 may 2023
)


class CohereGenerator(Generator):
    def __init__(self, name="command", generations=10):
        self.name = name
        self.fullname = f"Cohere {self.name}"
        self.generations = generations

        self.temperature = 0.750
        self.max_tokens = 200
        self.k = 0
        self.p = 0.75
        self.preset = None
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.stop = []

        self.generator_family_name = "Cohere"
        super().__init__(name)

        self.generator = cohere.Client(api_key)

    def generate(self, prompt):
        if self.generations > COHERE_GENERATION_LIMIT:
            self.generations = COHERE_GENERATION_LIMIT
            logging.debug(
                f"Cohere generation limit capped at {COHERE_GENERATION_LIMIT}"
            )
        try:
            response = self.generator.generate(
                model=self.name,
                prompt=prompt,
                temperature=self.temperature,
                num_generations=self.generations,
                max_tokens=self.max_tokens,
                preset=self.preset,
                k=self.k,
                p=self.p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                end_sequences=self.stop,
            )
        except:
            return []  # cohere client handles rate limiting ungracefully
        return [g.text for g in response]
