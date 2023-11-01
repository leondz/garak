#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""REST API generator interface

Generic Module for REST API connections
"""

import json
import logging
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
        self.uri = uri
        self.name = uri
        self.seed = garak._config.seed
        self.headers = {}
        self.method = "POST"
        self.req_template = "$INPUT"
        self.support_multi_generation = False  # not implemented in first version
        self.response_json = False
        self.response_json_field = "text"
        self.request_timeout = 10  # seconds
        self.ratelimit_codes = [429]
        self.escape_function = self._json_escape
        self.retry_5xx = True

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

            if "req_template_json_object" in garak._config.generator_options:
                self.req_template = json.dumps(
                    garak._config.generator_options["req_template_json_object"]
                )

            if (
                self.response_json
                and "response_json_field" in garak._config.generator_options
            ):
                self.response_json_field = garak._config.generator_options[
                    "response_json_field"
                ]

            if "name" in garak._config.generator_options:
                self.name = garak._config.generator_options["name"]

        self.fullname = f"REST {self.name}"

        self.rest_api_key = os.getenv("REST_API_KEY", default=None)

        super().__init__(uri, generations=generations)

    def _json_escape(self, text: str) -> str:
        """JSON escape a string"""
        # trim first & last "
        return json.dumps(text)[1:-1]

    def _populate_template(
        self, text: str, input: str, json_escape_key: bool = False
    ) -> str:
        """Replace template placeholders with values

        Interesting values are:
        * $KEY - the API key set as an object variable
        * $INPUT - the prompt text
        """
        if "$KEY" in text:
            if self.rest_api_key is None:
                raise ValueError(
                    "REST configuation specified API key but REST_API_KEY env var isn't set"
                )
            if json_escape_key:
                text = text.replace("$KEY", self.escape_function(self.rest_api_key))
            else:
                text = text.replace("$KEY", self.rest_api_key)
        return text.replace("$INPUT", self.escape_function(input))

    #        return text.replace("$INPUT", input)

    @backoff.on_exception(backoff.fibo, IOError, max_value=70)
    def _call_api(self, prompt):
        """Individual call to get a rest from the REST API

        :param prompt: the input to be plcaed into the request template and sent to the endpoint
        :type prompt: str
        """

        request_data = self._populate_template(self.req_template, prompt)

        request_headers = dict(self.headers)
        for k, v in self.headers.items():
            request_headers[k] = self._populate_template(v, prompt)

        resp = requests.post(
            self.name,
            data=request_data,
            headers=request_headers,
            timeout=self.request_timeout,
        )
        if resp.status_code in self.ratelimit_codes:
            raise IOError(f"Rate limited: {resp.status_code} - {resp.reason}")
        elif str(resp.status_code)[0] == "3":
            raise ConnectionError(
                f"REST URI redirection: {resp.status_code} - {resp.reason}"
            )
        elif str(resp.status_code)[0] == "4":
            raise ConnectionError(
                f"REST URI client error: {resp.status_code} - {resp.reason}"
            )
        elif str(resp.status_code)[0] == "5":
            error_msg = f"REST URI server error: {resp.status_code} - {resp.reason}"
            if self.retry_5xx:
                raise IOError(error_msg)
            else:
                raise ConnectionError(error_msg)

        if not self.response_json:
            return str(resp.content)
        else:
            try:
                response_object = json.loads(resp.content)
                return response_object[self.response_json_field]
            except json.decoder.JSONDecodeError as e:
                logging.warning(
                    "REST endpoint didn't return good JSON %s: got |%s|",
                    str(e),
                    resp.content,
                )
                return None

    def generate(self, prompt) -> List[str]:
        outputs = []
        generation_iterator = tqdm.tqdm(list(range(self.generations)), leave=False)
        generation_iterator.set_description("REST " + self.fullname[5:][-50:])
        if not self.support_multi_generation:
            for i in generation_iterator:
                result = self._call_api(prompt)
                if result is not None:
                    outputs.append(result)
        else:
            raise NotImplementedError(
                "Multiple generation per REST API call isn't implemented yet"
            )
        return outputs


default_class = "RestGenerator"
