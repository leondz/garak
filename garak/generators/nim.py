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
    """Wrapper for NVIDIA-hosted NIMs. Expects NIM_API_KEY environment variable."""

    supports_multiple_generations = False
    generator_family_name = "NIM"
    temperature = 0.1
    top_p = 0.7

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

            return response_body["choices"][0]["message"]["content"]


default_class = "NVHostedNimGenerator"
