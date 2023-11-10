#!/usr/bin/env python3
"""Replicate generator interface

Generator for https://replicate.com/

Put your replicate key in an environment variable called
REPLICATE_API_TOKEN. It's found on your Replicate account
page, https://replicate.com/account.

Text-output models are supported.
"""

import importlib
import os

import backoff
import replicate.exceptions
import tqdm

import garak._config
from garak.generators.base import Generator


class ReplicateGenerator(Generator):
    generator_family_name = "Replicate"
    temperature = 1
    top_p = 1.0
    repetition_penalty = 1
    supports_multiple_generations = False

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"Replicate {self.name}"
        self.seed = 320
        if garak._config.seed:
            self.seed = garak._config.seed

        super().__init__(name, generations=generations)

        if os.getenv("REPLICATE_API_TOKEN", default=None) is None:
            raise ValueError(
                'Put the Replicate API token in the REPLICATE_API_TOKEN environment variable (this was empty)\n \
                e.g.: export REPLICATE_API_TOKEN="r8-123XXXXXXXXXXXX"'
            )
        self.replicate = importlib.import_module("replicate")

    @backoff.on_exception(
        backoff.fibo, replicate.exceptions.ReplicateError, max_value=70
    )
    def _call_model(self, prompt):
        response_iterator = self.replicate.run(
            self.name,
            input={
                "prompt": prompt,
                "max_length": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty,
                "seed": self.seed,
            },
        )
        return "".join(response_iterator)


default_class = "ReplicateGenerator"
