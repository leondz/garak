# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""REST API generator interface

Generic Module for REST API connections
"""

import json
import logging
import os
from typing import List
import requests

import backoff

from garak import _config
from garak.generators.base import Generator


class RESTRateLimitError(Exception):
    """Raised when a rate limiting response is returned"""

    pass


class RestGenerator(Generator):
    """Generic API interface for REST models

    Uses the following options from _config.run.generators["rest.RestGenerator"]:
    * uri - (optional) the URI of the REST endpoint; this can also be passed
            in --model_name
    * name - a short name for this service; defaults to the uri
    * key_env_var - (optional) the name of the environment variable holding an
            API key, by default REST_API_KEY
    * req_template - a string where $KEY is replaced by env var REST_API_KEY
            and $INPUT is replaced by the prompt. Default is to just send the
            input text.
    * req_template_json_object - (optional) the request template as a Python
            object, to be serialised as a JSON string before replacements
    * method - a string describing the HTTP method, to be passed to the
            requests module; default "post".
    * headers - dict describing HTTP headers to be sent with the request
    * response_json - Is the response in JSON format? (bool)
    * response_json_field - (optional) Which field of the response JSON
            should be used as the output string? Default "text"
    * request_timeout - How many seconds should we wait before timing out?
            Default 20
    * ratelimit_codes - Which endpoint HTTP response codes should be caught
            as indicative of rate limiting and retried? List[int], default [429]

    Templates can be either a string or a JSON-serialisable Python object.
    Instance of "$INPUT" here are replaced with the prompt; instances of "$KEY"
    are replaced with the specified API key. If no key is needed, just don't
    put $KEY in a template.

    The $INPUT and $KEY placeholders can also be specified in header values.

    If we want to call an endpoint where the API key is defined in the value
    of an X-Authorization header, sending and receiving JSON where the prompt
    and response value are both under the "text" key, we'd define the service
    using something like:

    {"rest.RestGenerator":
        {
            "name": "example service",
            "uri": "https://example.ai/llm",
            "method": "post",
            "headers":{
                "X-Authorization": "$KEY",
            },
            "req_template_json_object":{
                "text":"$INPUT"
            },
            "response_json": true,
            "response_json_field": "text"
        }
    }

    To use this specification with garak, you can either pass the JSON as a
    strong option on the command line via --generator_options, or save the
    JSON definition into a file and pass the filename to
    --generator_option_file / -G. For example, if we save the above JSON into
    `example_service.json", we can invoke garak as:

    garak --model_type rest -G example_service.json

    This will load up the default RestGenerator and use the details in the
    JSON file to connect to the LLM endpoint.

    If you need something more flexible, add a new module or class and inherit
    from RestGenerator :)
    """

    generator_family_name = "REST"

    def __init__(self, uri=None, generations=10):
        self.uri = uri
        self.name = uri
        self.seed = _config.run.seed
        self.headers = {}
        self.method = "post"
        self.req_template = "$INPUT"
        self.supports_multiple_generations = False  # not implemented yet
        self.response_json = False
        self.response_json_field = "text"
        self.request_timeout = 20  # seconds
        self.ratelimit_codes = [429]
        self.escape_function = self._json_escape
        self.retry_5xx = True
        self.key_env_var = "REST_API_KEY"

        if "rest.RestGenerator" in _config.plugins.generators:
            for field in (
                "name",
                "uri",
                "key_env_var",
                "req_template",  # req_template_json is processed later
                "method",
                "headers",
                "response_json",  # response_json_field is processed later
                "request_timeout",
                "ratelimit_codes",
            ):
                if field in _config.plugins.generators["rest.RestGenerator"]:
                    setattr(
                        self,
                        field,
                        _config.plugins.generators["rest.RestGenerator"][field],
                    )

            if (
                "req_template_json_object"
                in _config.plugins.generators["rest.RestGenerator"]
            ):
                self.req_template = json.dumps(
                    _config.plugins.generators["rest.RestGenerator"][
                        "req_template_json_object"
                    ]
                )

            if (
                self.response_json
                and "response_json_field"
                in _config.plugins.generators["rest.RestGenerator"]
            ):
                self.response_json_field = _config.plugins.generators[
                    "rest.RestGenerator"
                ]["response_json_field"]

        if self.name is None:
            self.name = self.uri

        if self.uri is None:
            raise ValueError(
                "No REST endpoint URI definition found in either constructor param, JSON, or --model_name. Please specify one."
            )

        self.fullname = f"REST {self.name}"

        self.method = self.method.lower()
        if self.method not in (
            "get",
            "post",
            "put",
            "patch",
            "options",
            "delete",
            "head",
        ):
            logging.info(
                "RestGenerator HTTP method %s not supported, defaulting to 'post'",
                self.method,
            )
            self.method = "post"
        self.http_function = getattr(requests, self.method)

        self.rest_api_key = os.getenv(self.key_env_var, default=None)

        super().__init__(uri, generations=generations)

    def _json_escape(self, text: str) -> str:
        """JSON escape a string"""
        # trim first & last "
        return json.dumps(text)[1:-1]

    def _populate_template(
        self, template: str, text: str, json_escape_key: bool = False
    ) -> str:
        """Replace template placeholders with values

        Interesting values are:
        * $KEY - the API key set as an object variable
        * $INPUT - the prompt text

        $KEY is only set if the relevant environment variable is set; the
        default variable name is REST_API_KEY but this can be overridden.
        """
        output = template
        if "$KEY" in template:
            if self.rest_api_key is None:
                raise ValueError(
                    f"Template requires an API key but {self.key_env_var} env var isn't set"
                )
            if json_escape_key:
                output = output.replace("$KEY", self.escape_function(self.rest_api_key))
            else:
                output = output.replace("$KEY", self.rest_api_key)
        return output.replace("$INPUT", self.escape_function(text))

    # we'll overload IOError as the rate limit exception
    @backoff.on_exception(backoff.fibo, RESTRateLimitError, max_value=70)
    def _call_model(self, prompt: str, generations_this_call: int = 1):
        """Individual call to get a rest from the REST API

        :param prompt: the input to be placed into the request template and sent to the endpoint
        :type prompt: str
        """

        request_data = self._populate_template(self.req_template, prompt)

        request_headers = dict(self.headers)
        for k, v in self.headers.items():
            request_headers[k] = self._populate_template(v, prompt)

        resp = self.http_function(
            self.uri,
            data=request_data,
            headers=request_headers,
            timeout=self.request_timeout,
        )
        if resp.status_code in self.ratelimit_codes:
            raise RESTRateLimitError(
                f"Rate limited: {resp.status_code} - {resp.reason}"
            )

        elif str(resp.status_code)[0] == "3":
            raise NotImplementedError(
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


default_class = "RestGenerator"
