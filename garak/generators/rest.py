#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""REST API generator interface

Generic Module for REST API connections
"""

import json
import os
import requests
from typing import List

import backoff
import tqdm

import garak._config
from garak.generators.base import Generator


class RestGenerator(Generator):
    """Generic API interface for REST models

    Expects the following options from _config.generator_options:
    * headers - dict
    * req_template - a string where $KEY is replaced by env var REST_API_KEY
                     and $INPUT is replaced by the prompt
    * response - dict {response_json: True, response_json_field: "text"}
    """

    generator_family_name = "REST"

    def __init__(self, uri, generations=10):
        self.name = uri
        self.fullname = f"REST {self.name}"
        self.seed = garak._config.seed
        self.headers = {}
        self.method = "POST"
        self.req_template = "$INPUT"
        self.support_multi_generation = False
        self.response_json = False
        self.response_json_field = "text"
        self.request_timeout = 10  # seconds
        self.ratelimit_codes = [429]

        if "generator_options" in dir(garak._config):
            for field in (
                "headers",
                "response_json",
                "req_template",
                "method",
                "response_timeout",
                "ratelimit_codes",
            ):
                if field in garak._config.generator_options:
                    setattr(self, field, garak._config.generator_options[field])

            if (
                self.response_json
                and "response_json_field" in garak._config.generator_options
            ):
                self.response_json_field = garak._config.generator_options[
                    "response_json_field"
                ]

        self.rest_api_key = os.getenv("REST_API_KEY", default="")

        super().__init__(uri, generations=generations)

    def _populate_template(self, text: str, input: str) -> str:
        return text.replace("$KEY", self.rest_api_key).replace("$INPUT", input)

    @backoff.on_exception(backoff.fibo, IOError, max_value=70)
    def _call_api(self, prompt):
        request_data = self._populate_template(self.req_template, prompt)

        request_headers = dict(self.headers)
        for k, v in self.headers.items():
            request_headers[k] = self._populate_template(v, prompt)

        resp = requests.post(
            self.name,
            data=request_data,
            headers=self.headers,
            timeout=self.request_timeout,
        )
        if resp.status_code in self.ratelimit_codes:
            raise IOError(f"Rate limited: {resp.status_code} - {resp.reason}")
        elif str(resp.status_code)[0] == "3":
            raise ConnectionError(
                f"URI redirection: {resp.status_code} - {resp.reason}"
            )
        elif str(resp.status_code)[0] == "4":
            raise ConnectionError(
                f"URI client error: {resp.status_code} - {resp.reason}"
            )
        elif str(resp.status_code)[0] == "5":
            raise ConnectionError(
                f"URI server error: {resp.status_code} - {resp.reason}"
            )

        if not self.response_json:
            return str(resp.content)
        else:
            response_object = json.loads(resp.content)
            return response_object[self.response_json_field]

    def generate(self, prompt) -> List[str]:
        outputs = []
        generation_iterator = tqdm.tqdm(list(range(self.generations)), leave=False)
        generation_iterator.set_description("REST " + self.fullname[5:][-50:])
        if not self.support_multi_generation:
            for i in generation_iterator:
                outputs.append(self._call_api(prompt))
        return outputs


default_class = "RestGenerator"
