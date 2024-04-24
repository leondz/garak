"""Cohere AI model support

Support for Cohere's text generation API. Uses the command model by default,
but just supply the name of another either on the command line or as the
constructor param if you want to use that. You'll need to set an environment
variable called COHERE_API_KEY to your Cohere API key, for this generator.
"""


import logging
import os
from typing import List, Union

import backoff
import cohere
import tqdm

from garak.generators.base import Generator


COHERE_GENERATION_LIMIT = (
    5  # c.f. https://docs.cohere.com/reference/generate 18 may 2023
)


class CohereGenerator(Generator):
    """Interface to Cohere's python library for their text2text model.

    Expects API key in COHERE_API_KEY environment variable.
    """

    supports_multiple_generations = True
    temperature = 0.750
    k = 0
    p = 0.75
    preset = None
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = []
    generator_family_name = "Cohere"

    def __init__(self, name="command", generations=10):
        self.name = name
        self.fullname = f"Cohere {self.name}"
        self.generations = generations

        super().__init__(name, generations=generations)

        api_key = os.getenv("COHERE_API_KEY", default=None)
        if api_key is None:
            raise ValueError(
                'Put the Cohere API key in the COHERE_API_KEY environment variable (this was empty)\n \
                e.g.: export COHERE_API_KEY="XXXXXXX"'
            )
        logging.debug(
            "Cohere generation request limit capped at %s", COHERE_GENERATION_LIMIT
        )
        self.generator = cohere.Client(api_key)

    @backoff.on_exception(backoff.fibo, cohere.error.CohereAPIError, max_value=70)
    def _call_cohere_api(self, prompt, request_size=COHERE_GENERATION_LIMIT):
        """as of jun 2 2023, empty prompts raise:
        cohere.error.CohereAPIError: invalid request: prompt must be at least 1 token long
        filtering exceptions based on message instead of type, in backoff, isn't immediately obvious
        - on the other hand blank prompt / RTP shouldn't hang forever
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

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> Union[List[str], str, None]:
        """Cohere's _call_model does sub-batching before calling,
        and so manages chunking internally"""
        quotient, remainder = divmod(generations_this_call, COHERE_GENERATION_LIMIT)
        request_sizes = [COHERE_GENERATION_LIMIT] * quotient
        if remainder:
            request_sizes += [remainder]
        outputs = []
        generation_iterator = tqdm.tqdm(request_sizes, leave=False)
        generation_iterator.set_description(self.fullname)
        for request_size in generation_iterator:
            outputs += self._call_cohere_api(prompt, request_size=request_size)
        return outputs


default_class = "CohereGenerator"
