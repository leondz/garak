# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""NVCF LLM interface"""

import json
import logging
import os
import time
from typing import List, Union

import backoff
import requests

from garak import _config
from garak.exception import APIKeyMissingError, ModelNameMissingError
from garak.generators.base import Generator


class NvcfChat(Generator):
    """Wrapper for NVIDIA Cloud Functions Chat models via NGC. Expects NVCF_API_KEY environment variable."""

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
        self.fullname = (
            f"{self.generator_family_name} {self.__class__.__name__} {self.name}"
        )
        self.seed = _config.run.seed

        if self.name is None:
            raise ModelNameMissingError(
                "Please specify a function identifier in model name (-n)"
            )

        self.invoke_url = self.invoke_url_base + name

        super().__init__(name, generations=generations)

        self.api_key = os.getenv("NVCF_API_KEY", default=None)
        if self.api_key is None:
            raise APIKeyMissingError(
                'Put the NVCF API key in the NVCF_API_KEY environment variable (this was empty)\n \
                e.g.: export NVCF_API_KEY="nvapi-xXxXxXxXxXxXxXxXxXxX"'
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _build_payload(self, prompt) -> dict:

        payload = {
            "messages": [{"content": prompt, "role": "user"}],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        return payload

    def _extract_text_output(self, response) -> str:
        return [c["message"]["content"] for c in response["choices"]]

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
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:

        session = requests.Session()

        payload = self._build_payload(prompt)

        ## NB config indexing scheme to be deprecated
        config_class = f"nvcf.{self.__class__.__name__}"
        if config_class in _config.plugins.generators:
            if "payload" in _config.plugins.generators[config_class]:
                for k, v in _config.plugins.generators[config_class]["payload"].items():
                    payload[k] = v

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
            logging.warning("nvcf : payload %s", repr(payload))
            logging.warning("nvcf : returned error body %s", response.content)
            if response.status_code == 400 and prompt == "":
                # error messages for refusing a blank prompt are fragile and include multi-level wrapped JSON, so this catch is a little broad
                return [None]
            if response.status_code >= 500:
                if response.status_code == 500 and json.loads(response.content)[
                    "detail"
                ].startswith("Input value error"):
                    logging.warning("nvcf : skipping this prompt")
                    return [None]
                else:
                    response.raise_for_status()
            else:
                logging.warning("nvcf : skipping this prompt")
                return [None]

        else:
            response_body = response.json()

            return self._extract_text_output(response_body)


class NvcfCompletion(NvcfChat):
    """Wrapper for NVIDIA Cloud Functions Completion models via NGC. Expects NVCF_API_KEY environment variables."""

    def _build_payload(self, prompt) -> dict:

        payload = {
            "prompt": prompt,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        return payload

    def _extract_text_output(self, response) -> str:
        return [c["text"] for c in response["choices"]]


DEFAULT_CLASS = "NvcfChat"
