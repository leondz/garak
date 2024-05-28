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

    temperature = 0.750  # defaults to 0.3
    frequency_penalty = 0.0
    presence_penalty = 0.0
    stop = []
    k = 0
    p = 0.75
    generator_family_name = "CohereChat"

    # Out of scope at present
    # conversation_id
    # prompt_truncation
    # connectors
    # citation_quality
    # max_tokens
    # max_input_tokens

    def __init__(self, generations=10):
        self.fullname = "Cohere Chat"
        self.generations = generations

        super().__init__(generations=generations)

        api_key = os.getenv("COHERE_API_KEY", default=None)
        if api_key is None:
            raise APIKeyMissingError(
                'Put the Cohere API key in the COHERE_API_KEY environment variable (this was empty)\n \
                e.g.: export COHERE_API_KEY="XXXXXXX https://docs.cohere.com/reference/checkapikey"'
            )
        logging.debug(
            "Cohere chat generation request limit capped at %s", COHERE_GENERATION_LIMIT
        )
        self.generator = cohere.Client(api_key)

    @backoff.on_exception(backoff.fibo, cohere.error.CohereAPIError, max_value=70)
    def _call_cohere_api(self, prompt, request_size=COHERE_GENERATION_LIMIT):
        response = self.generator.chat(prompt=prompt, temperature=self.temperature, max_tokens=request_size,
                                       frequency_penalty=self.frequency_penalty, presence_penalty=self.presence_penalty,
                                       end_sequences=self.stop)
        return [g.text for g in response]

    def _call_model(self, prompt: str, generations_this_call: int = 1) -> List[Union[str, None]]:
        outputs = self._call_cohere_api(prompt)
        return outputs


DEFAULT_CLASS = "CohereChatGenerator"
