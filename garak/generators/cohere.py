#!/usr/bin/env python3

import logging
import os

import backoff
import cohere
import tqdm

from garak.generators.base import Generator


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

        api_key = os.getenv("COHERE_API_KEY", default=None)
        if api_key == None:
            raise Exception(
                'Put the Cohere API key in the COHERE_API_KEY environment variable (this was empty)\n \
                e.g.: export COHERE_API_KEY="XXXXXXX"'
            )
        logging.debug(
            f"Cohere generation request limit capped at {COHERE_GENERATION_LIMIT}"
        )
        self.generator = cohere.Client(api_key)

    @backoff.on_exception(backoff.fibo, cohere.error.CohereAPIError, max_value=70)
    def _call_api(self, prompt, request_size=COHERE_GENERATION_LIMIT):
        """as of jun 2 2023, empty prompts raise:
        cohere.error.CohereAPIError: invalid request: prompt must be at least 1 token long
        filtering exceptions based on message instead of type, in backoff, isn't immediately obvious
        - on the other hand blankprompt / RTP shouldn't hang forever
        """
        if prompt == "":
            return [""] * request_size
        else:
            response = self.generator.generate(
                model=self.name,
                prompt=prompt,
                temperature=self.temperature,
                num_generations=request_size,
                max_tokens=self.max_tokens,
                preset=self.preset,
                k=self.k,
                p=self.p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                end_sequences=self.stop,
            )
            return [g.text for g in response]

    def generate(self, prompt):
        quotient, remainder = divmod(self.generations, COHERE_GENERATION_LIMIT)
        request_sizes = [COHERE_GENERATION_LIMIT] * quotient + [remainder]
        outputs = []
        generation_iterator = tqdm.tqdm(request_sizes, leave=False)
        generation_iterator.set_description(self.fullname)
        for request_size in generation_iterator:
            outputs += self._call_api(prompt, request_size=request_size)
        return outputs


default_class = "CohereGenerator"
