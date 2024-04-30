#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NVIDIA Inference Microservice LLM interface"""

import json
import logging
import os
import requests
from typing import Union

import backoff

from garak import _config
from garak.generators.base import Generator


class NVHostedNimGenerator(Generator):
    """Wrapper for NVIDIA-hosted NIMs. Expects NIM_API_KEY environment variable.

    Uses the [OpenAI-compatible API](https://docs.nvidia.com/ai-enterprise/nim-llm/latest/openai-api.html)
    via direct HTTP request.

    To get started with this generator:
    #. Visit [https://build.nvidia.com/explore/reasoning](build.nvidia.com/explore/reasoning)
    and find the LLM you'd like to use.
    #. On the page for the LLM you want to use (e.g. [mixtral-8x7b-instruct](https://build.nvidia.com/mistralai/mixtral-8x7b-instruct)),
    click "Get API key" key above the code snippet. You may need to create an
    account. Copy this key.
    #. In your console, Set the ``NIM_API_KEY`` variable to this API key. On
    Linux, this might look like ``export NIM_API_KEY="nvapi-xXxXxXx"``.
    #. Run garak, setting ``--model_name`` to ``nim`` and ``--model_type`` to
    the name of the model on [build.nvidia.com](https://build.nvidia.com/)
    - e.g. ``mistralai/mixtral-8x7b-instruct-v0.1``.

    """

    supports_multiple_generations = False
    generator_family_name = "NIM"
    temperature = 0.1
    top_p = 0.7
    top_k = 0  # top_k is hard set to zero as of 24.04.30

    url = "https://integrate.api.nvidia.com/v1/chat/completions"

    timeout = 60

    def __init__(self, name=None, generations=10):
        self.name = name
        self.fullname = f"NIM {self.name}"
        self.seed = _config.run.seed

        if self.name is None:
            raise ValueError("Please specify a NIM in model name (-n)")

        super().__init__(name, generations=generations)

        self.api_key = os.getenv("NIM_API_KEY", default=None)
        if self.api_key is None:
            raise ValueError(
                'Put the NIM API key in the NIM_API_KEY environment variable (this was empty)\n \
                e.g.: export NIM_API_KEY="nvapi-xXxXxXxXxXxXxXxXxXxX"'
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @backoff.on_exception(
        backoff.fibo,
        (
            AttributeError,
            TimeoutError,
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
        ),
        max_value=70,
    )
    def _call_model(self, prompt: str) -> Union[str, None]:
        if prompt == "":
            return ""

        payload = {
            "model": self.name,
            "max_tokens": self.max_tokens,
            "stream": False,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "messages": [{"role": "user", "content": prompt}],
        }

        if self.seed is not None:
            payload["seed"] = self.seed

        response = requests.post(self.url, json=payload, headers=self.headers)

        if 400 <= response.status_code <= 599:
            logging.warning("nim : returned error code %s", response.status_code)
            logging.warning("nim : returned error body %s", response.content)
            if response.status_code >= 500:
                if response.status_code == 500 and json.loads(response.content)[
                    "detail"
                ].startswith("Input value error"):
                    logging.warning("nim : skipping this prompt")
                    return None
                else:
                    response.raise_for_status()
            else:
                logging.warning("nim : skipping this prompt")
                return None

        else:
            response_body = response.json()

            # per https://docs.nvidia.com/ai-enterprise/nim-llm/latest/openai-api.html
            # `n>1` is not supported, so the [0] is safe.
            #
            return response_body["choices"][0]["message"]["content"]


default_class = "NVHostedNimGenerator"
