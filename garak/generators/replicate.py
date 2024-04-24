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

from garak import _config
from garak.generators.base import Generator


class ReplicateGenerator(Generator):
    """
    Interface for public endpoints of models hosted in Replicate (replicate.com).
    Expects API key in REPLICATE_API_TOKEN environment variable.
    """

    generator_family_name = "Replicate"
    temperature = 1
    top_p = 1.0
    repetition_penalty = 1
    supports_multiple_generations = False

    def __init__(self, name, generations=10):
        self.name = name
        self.fullname = f"{self.generator_family_name} {self.name}"
        self.seed = 9
        if hasattr(_config.run, "seed") and _config.run.seed is not None:
            self.seed = _config.run.seed

        super().__init__(name, generations=generations)

        if os.getenv("REPLICATE_API_TOKEN", default=None) is None:
            raise ValueError(
                '🛑 Put the Replicate API token in the REPLICATE_API_TOKEN environment variable (this was empty)\n \
                e.g.: export REPLICATE_API_TOKEN="r8-123XXXXXXXXXXXX"'
            )
        self.replicate = importlib.import_module("replicate")

    @backoff.on_exception(
        backoff.fibo, replicate.exceptions.ReplicateError, max_value=70
    )
    def _call_model(self, prompt: str, generations_this_call: int = 1):
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


class InferenceEndpoint(ReplicateGenerator):
    """
    Interface for private Replicate endpoints.
    Expects `name` in the format of `username/deployed-model-name`.
    """

    @backoff.on_exception(
        backoff.fibo, replicate.exceptions.ReplicateError, max_value=70
    )
    def _call_model(self, prompt):
        deployment = self.replicate.deployments.get(self.name)
        prediction = deployment.predictions.create(
            input={
                "prompt": prompt,
                "max_length": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty,
            },
        )
        prediction.wait()
        try:
            response = "".join(prediction.output)
        except TypeError:
            raise IOError(
                "Replicate endpoint didn't generate a response. Make sure the endpoint is active."
            )
        return response


default_class = "ReplicateGenerator"
