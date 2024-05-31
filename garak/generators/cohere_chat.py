"""Cohere AI model support

Support for Cohere's text generation API via updated endpoint /chat. Uses the command-r model by default,
but just supply the name of another either on the command line or as the
constructor param if you want to use that. You'll need to set an environment
variable called COHERE_API_KEY to your Cohere API key, for this generator.

https://docs.cohere.com/reference/chat
Currently does not support multiple generations.

See https://docs.cohere.com/reference/list-models for models
"""

import logging
import os
import importlib
from typing import List, Union

import backoff
import cohere
import tqdm

from garak.exception import APIKeyMissingError
from garak.generators.base import Generator


class CohereGenerator(Generator):
    """Interface to Cohere's python library for their text2text model.
    Expects API key in COHERE_API_KEY environment variable.
    """

    generator_family_name = "CohereChat"
    temperature = 0.750  # defaults to 0.3
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = []
    k = 0
    p = 0.75
    supports_multiple_generations = False

    # Out of scope at present
    # conversation_id
    # prompt_truncation
    # connectors
    # citation_quality
    # max_tokens
    # max_input_tokens

    def __init__(self, fullname, generations=10):
        self.seed = 9
        if hasattr(_config.run, "seed") and _config.run.seed is not None:
            self.seed = _config.run.seed

        super().__init__(name, generations=generations)

        api_key = os.getenv("COHERE_API_KEY", default=None)
        if api_key is None:
            raise APIKeyMissingError(
                'Put the Cohere API key in the COHERE_API_KEY environment variable (this was empty)\n \
                e.g.: export COHERE_API_KEY="XXXXXXX"'
            )
        logging.debug(
            "Cohere generation request limit capped at %s", COHERE_GENERATION_LIMIT
        )
        self.generator = cohere.Client(api_key)

    @backoff.on_exception(backoff.fibo, cohere.error.CohereAPIError, max_value=70)
    def _call_cohere_api(self, prompt, request_size=COHERE_GENERATION_LIMIT):
        """
        cohere.error.CohereAPIError: invalid request: prompt must be at least 1 token long
        filtering exceptions based on message instead of type, in backoff, isn't immediately obvious
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
    ) -> List[Union[str, None]]:
        """Cohere's _call_model does sub-batching before calling,
        and so manages chunking internally"""
        quotient, remainder = divmod(
            generations_this_call, COHERE_GENERATION_LIMIT)
        request_sizes = [COHERE_GENERATION_LIMIT] * quotient
        if remainder:
            request_sizes += [remainder]
        outputs = []
        generation_iterator = tqdm.tqdm(request_sizes, leave=False)
        generation_iterator.set_description(self.fullname)
        for request_size in generation_iterator:
            outputs += self._call_cohere_api(prompt, request_size=request_size)
        return outputs


DEFAULT_CLASS = "CohereChatGenerator"
