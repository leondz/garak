# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""REST API generator interface

Generic Module for REST API connections
"""

import json
import logging
from typing import List, Union
import requests
import os

import backoff
import jsonpath_ng
from jsonpath_ng.exceptions import JsonPathParserError

from garak import _config
from garak.exception import APIKeyMissingError, RateLimitHit
from garak.generators.base import Generator


class RestGenerator(Generator):
    """Generic API interface for REST models

    Uses the following options from ``_config.plugins.generators["rest.RestGenerator"]``:
    * ``uri`` - (optional) the URI of the REST endpoint; this can also be passed
            in --model_name
    * ``name`` - a short name for this service; defaults to the uri
    * ``key_env_var`` - (optional) the name of the environment variable holding an
            API key, by default REST_API_KEY
    * ``req_template`` - a string where the text ``$KEY`` is replaced by env
            var REST_API_KEY and ``$INPUT`` is replaced by the prompt. Default is to
            just send the input text.
    * ``req_template_json_object`` - (optional) the request template as a Python
            object, to be serialised as a JSON string before replacements
    * ``method`` - a string describing the HTTP method, to be passed to the
            requests module; default "post".
    * ``headers`` - dict describing HTTP headers to be sent with the request
    * ``response_json`` - Is the response in JSON format? (bool)
    * ``response_json_field`` - (optional) Which field of the response JSON
            should be used as the output string? Default ``text``. Can also
            be a JSONPath value, and ``response_json_field`` is used as such
            if it starts with ``$``.
    * ``request_timeout`` - How many seconds should we wait before timing out?
            Default 20
    * ``ratelimit_codes`` - Which endpoint HTTP response codes should be caught
            as indicative of rate limiting and retried? ``List[int]``, default ``[429]``

    Templates can be either a string or a JSON-serialisable Python object.
    Instance of ``$INPUT`` here are replaced with the prompt; instances of ``$KEY``
    are replaced with the specified API key. If no key is needed, just don't
    put ``$KEY`` in a template.

    The ``$INPUT`` and ``$KEY`` placeholders can also be specified in header values.

    If we want to call an endpoint where the API key is defined in the value
    of an ``X-Authorization`` header, sending and receiving JSON where the prompt
    and response value are both under the ``text`` key, we'd define the service
    using something like: ::

    .. code-block:: JSON
      :linenos:

        {
            "rest": {
                "RestGenerator": {
                    "name": "example service",
                    "uri": "https://example.ai/llm",
                    "method": "post",
                    "headers": {
                        "X-Authorization": "$KEY",
                    },
                    "req_template_json_object": {
                        "text": "$INPUT"
                    },
                    "response_json": true,
                    "response_json_field": "text"
                }
            }
        }

    NB. ``response_json_field`` can also be a JSONPath, for JSON responses where
    the target text is not in a top level field. It is treated as a JSONPath
    when ``response_json_field`` starts with ``$``.

    To use this specification with garak, you can either pass the JSON as a
    strong option on the command line via --generator_options, or save the
    JSON definition into a file and pass the filename to
    ``--generator_option_file`` / ``-G``. For example, if we save the above
    JSON into ``example_service.json``, we can invoke garak as: ::

      garak --model_type rest -G example_service.json

    This will load up the default ``RestGenerator`` and use the details in the
    JSON file to connect to the LLM endpoint.

    If you need something more flexible, add a new module or class and inherit
    from RestGenerator :)
    """

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "headers": {},
        "method": "post",
        "ratelimit_codes": [429],
        "response_json": False,
        "response_json_field": None,
        "req_template": "$INPUT",
        "request_timeout": 20,
        "proxies": None,
        "verify_ssl": True,
    }

    ENV_VAR = "REST_API_KEY"
    generator_family_name = "REST"

    _supported_params = (
        "api_key",
        "name",
        "uri",
        "key_env_var",
        "req_template",
        "req_template_json",
        "context_len",
        "max_tokens",
        "method",
        "headers",
        "response_json",
        "response_json_field",
        "req_template_json_object",
        "request_timeout",
        "ratelimit_codes",
        "temperature",
        "top_k",
        "proxies",
        "verify_ssl",
    )

    def __init__(self, uri=None, config_root=_config):
        self.uri = uri
        self.name = uri
        self.seed = _config.run.seed
        self.supports_multiple_generations = False  # not implemented yet
        self.escape_function = self._json_escape
        self.retry_5xx = True
        self.key_env_var = self.ENV_VAR if hasattr(self, "ENV_VAR") else None
        self.need_token_refresh = False

        # load configuration since super.__init__ has not been called
        self._load_config(config_root)

        # Load the token refresh configuration
        if hasattr(config_root.transient.cli_args, "token_refresh_config"):
            self.token_refresh_path = config_root.transient.cli_args.token_refresh_config
            with open(self.token_refresh_path, "r") as f:
                self.token_refresh_config = json.load(f)
            if not isinstance(self.token_refresh_config["method"], str):
                raise ValueError("token_refresh_config set but does not contain method")
            if not isinstance(self.token_refresh_config["required_secrets"], list):
                raise ValueError("token_refresh_config set but does not contain required_secrets list")
            
            if len(self.token_refresh_config["required_secrets"]) == 0:
                raise ValueError("token_refresh_config required_secrets list is empty")
            
            self.token_refresh_http_function = getattr(requests, self.token_refresh_config["method"].lower())

            secrets = {}
            for secret in self.token_refresh_config["required_secrets"]:
                if secret in os.environ:
                    secrets[secret] = os.environ[secret]
                else:
                    raise ValueError(f"token_refresh_config required secret: {secret} not found in environment")
            self.token_refresh_config["secrets"] = secrets


        if (hasattr(self, "req_template_json_object") and self.req_template_json_object is not None):
            self.req_template = json.dumps(self.req_template_json_object)

        if self.response_json:
            if self.response_json_field is None:
                raise ValueError(
                    "RestGenerator response_json is True but response_json_field isn't set"
                )
            if not isinstance(self.response_json_field, str):
                raise ValueError("response_json_field must be a string")
            if self.response_json_field == "":
                raise ValueError(
                    "RestGenerator response_json is True but response_json_field is an empty string. If the root object is the target object, use a JSONPath."
                )

        if self.name is None:
            self.name = self.uri

        if self.uri is None:
            raise ValueError(
                "No REST endpoint URI definition found in either constructor param, JSON, or --model_name. Please specify one."
            )

        self.fullname = f"{self.generator_family_name} {self.name}"

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

        # validate jsonpath
        if self.response_json and self.response_json_field:
            try:
                self.json_expr = jsonpath_ng.parse(self.response_json_field)
            except JsonPathParserError as e:
                logging.CRITICAL(
                    "Couldn't parse response_json_field %s", self.response_json_field
                )
                raise e

        super().__init__(self.name, config_root=config_root)

    def _validate_env_var(self):
        key_match = "$KEY"
        header_requires_key = False
        for _k, v in self.headers.items():
            if key_match in v:
                header_requires_key = True
        if "$KEY" in self.req_template or header_requires_key:
            return super()._validate_env_var()

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
            if self.api_key is None:
                raise APIKeyMissingError(
                    f"Template requires an API key but {self.key_env_var} env var isn't set"
                )
            if json_escape_key:
                output = output.replace("$KEY", self.escape_function(self.api_key))
            else:
                output = output.replace("$KEY", self.api_key)
        return output.replace("$INPUT", self.escape_function(text))

    # we'll overload IOError as the rate limit exception
    @backoff.on_exception(backoff.fibo, RateLimitHit, max_value=70)
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        """Individual call to get a rest from the REST API

        :param prompt: the input to be placed into the request template and sent to the endpoint
        :type prompt: str
        """
        if self.need_token_refresh:
            token_refresh_data_kw = "params" if self.token_refresh_http_function == requests.get else "data"
            token_refresh_request_headers = dict(self.token_refresh_config["headers"])
            token_refresh_request_data = self._populate_token_refresh(self.token_refresh_config["data"])
            token_refresh_req_kArgs = {
                token_refresh_data_kw: token_refresh_request_data,
                "headers": token_refresh_request_headers,
                "timeout": self.request_timeout,
                "proxies": self.proxies,
                "verify": self.verify_ssl,
            }

            # TODO: add error handling
            token_refresh_resp = self.token_refresh_http_function(self.token_refresh_config['uri'], **token_refresh_req_kArgs)
            token_refresh_response_object = json.loads(token_refresh_resp.content)
            field_path_expr = jsonpath_ng.parse(self.token_refresh_config["response_json_field"])
            token_refresh_json_extraction_results = field_path_expr.find(token_refresh_response_object)
            self.api_key = token_refresh_json_extraction_results[0].value
            self.need_token_refresh = False

        request_data = self._populate_template(self.req_template, prompt)

        request_headers = dict(self.headers)
        for k, v in self.headers.items():
            request_headers[k] = self._populate_template(v, prompt)

        # the prompt should not be sent via data when using a GET request. Prompt should be
        # serialized as parameters, in general a method could be created to add
        # the prompt data to a request via params or data based on the action verb
        data_kw = "params" if self.http_function == requests.get else "data"
        req_kArgs = {
                data_kw: request_data,
                "headers": request_headers,
                "timeout": self.request_timeout,
                "proxies": self.proxies,
            }
        resp = self.http_function(self.uri, **req_kArgs)
        if resp.status_code in self.ratelimit_codes:
            raise RateLimitHit(f"Rate limited: {resp.status_code} - {resp.reason}")

        elif str(resp.status_code)[0] == "3":
            raise NotImplementedError(
                f"REST URI redirection: {resp.status_code} - {resp.reason}"
            )

        elif str(resp.status_code)[0] == "4":
            # Token is expired, refresh it
            if resp.status_code == 401:
                self.need_token_refresh = True
                raise RateLimitHit(f"Rate limited: {resp.status_code} - {resp.reason}")
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
            return [str(resp.text)]

        response_object = json.loads(resp.content)

        # if response_json_field starts with a $, treat is as a JSONPath
        assert (
            self.response_json
        ), "response_json must be True at this point; if False, we should have returned already"
        assert isinstance(
            self.response_json_field, str
        ), "response_json_field must be a string"
        assert (
            len(self.response_json_field) > 0
        ), "response_json_field needs to be complete if response_json is true; ValueError should have been raised in constructor"
        if self.response_json_field[0] != "$":
            response = [response_object[self.response_json_field]]
        else:
            field_path_expr = jsonpath_ng.parse(self.response_json_field)
            responses = field_path_expr.find(response_object)
            if len(responses) == 1:
                response_value = responses[0].value
                if isinstance(response_value, str):
                    response = [response_value]
                elif isinstance(response_value, list):
                    response = response_value
            elif len(responses) > 1:
                response = [r.value for r in responses]
            else:
                logging.error(
                    "RestGenerator JSONPath in response_json_field yielded nothing. Response content: %s"
                    % repr(resp.content)
                )
                return [None]

        return response


DEFAULT_CLASS = "RestGenerator"
