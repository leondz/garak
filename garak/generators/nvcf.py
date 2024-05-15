# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NVCF LLM interface"""

import json
import logging
import os
import time

import backoff
import requests

from garak import _config
from garak.generators.base import Generator


class NvcfGenerator(Generator):
    """Wrapper for NVIDIA Cloud Functions via NGC. Expects NGC_API_KEY and ORG_ID environment variables."""

    supports_multiple_generations = False
    generator_family_name = "NVCF"
    temperature = 0.2
    top_p = 0.7

    fetch_url_format = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/"
    invoke_url_base = "https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/"

    extra_nvcf_logging = False

    timeout = 60

    def __init__(self, name=None, generations=10):
        self.name = name
        self.fullname = f"NVCF {self.name}"
        self.seed = _config.run.seed

        if self.name is None:
            raise ValueError("Please specify a function identifier in model namne (-n)")

        self.invoke_url = self.invoke_url_base + name

        super().__init__(name, generations=generations)

        self.api_key = os.getenv("NVCF_API_KEY", default=None)
        if self.api_key is None:
            raise ValueError(
                'Put the NVCF API key in the NVCF_API_KEY environment variable (this was empty)\n \
                e.g.: export NVCF_API_KEY="nvapi-xXxXxXxXxXxXxXxXxXxX"'
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
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
    def _call_model(self, prompt: str, generations_this_call: int = 1) -> str:
        if prompt == "":
            return ""

        session = requests.Session()

        payload = {
            "messages": [{"content": prompt, "role": "user"}],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        if self.seed is not None:
            payload["seed"] = self.seed

        request_time = time.time()
        response = session.post(self.invoke_url, headers=self.headers, json=payload)

        while response.status_code == 202:
            if time.time() > request_time + self.timeout:
                raise TimeoutError("NVCF Request timed out")
            request_id = response.headers.get("NVCF-REQID")
            if request_id is None:
                msg = "Got HTTP 202 but no NVCF-REQID was returned"
                logging.info("nvcf : %s", msg)
                raise AttributeError(msg)
            fetch_url = self.fetch_url_format + request_id
            response = session.get(fetch_url, headers=self.headers)

        if 400 <= response.status_code < 600:
            logging.warning("nvcf : returned error code %s", response.status_code)
            logging.warning("nvcf : returned error body %s", response.content)
            if response.status_code >= 500:
                if response.status_code == 500 and json.loads(response.content)[
                    "detail"
                ].startswith("Input value error"):
                    logging.warning("nvcf : skipping this prompt")
                    return None
                else:
                    response.raise_for_status()
            else:
                logging.warning("nvcf : skipping this prompt")
                return None

        else:
            response_body = response.json()

            return response_body["choices"][0]["message"]["content"]


default_class = "NvcfGenerator"
