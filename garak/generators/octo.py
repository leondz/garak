#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""OctoML LLM interface"""


import os

import backoff
import octoai.errors

import garak._config
from garak.generators.base import Generator


class OctoGenerator(Generator):
    """Interface for OctoML models

    Pass the model URL as the name, e.g. https://llama-2-70b-chat-demo-kk0powt97tmb.octoai.run/v1/chat/completions

    This module tries to guess the internal model name in self.octo_model.
    We don't have access to private model so don't know the format.
    If garak guesses wrong, please please open a ticket.
    """

    generator_family_name = "OctoML"
    supports_multiple_generations = False

    def __init__(self, name, generations=10):
        from octoai.client import Client

        self.name = name
        self.fullname = f"{self.generator_family_name} {self.name}"
        self.seed = 9
        if garak._config.seed:
            self.seed = garak._config.seed

        self.octo_model = "-".join(
            self.name.replace("-demo", "").replace("https://", "").split("-")[:-1]
        )

        super().__init__(name, generations=generations)

        if os.getenv("OCTO_API_KEY", default=None) is None:
            raise ValueError(
                'Put the Replicate API token in the OCTOAI_TOKEN environment variable (this was empty)\n \
                e.g.: export OCTOAI_TOKEN="kjhasdfuhasi8djgh"'
            )
        self.octoml = Client(token=os.getenv("OCTO_API_KEY", default=None))

    @backoff.on_exception(backoff.fibo, octoai.errors.OctoAIServerError, max_value=70)
    def _call_model(self, prompt):
        outputs = self.octoml.infer(
            endpoint_url=self.name,
            inputs={
                "model": self.octo_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "max_tokens": self.max_tokens,
                "stream": False,
            },
        )
        return outputs.get("choices")[0].get("message").get("content")


default_class = "OctoGenerator"
