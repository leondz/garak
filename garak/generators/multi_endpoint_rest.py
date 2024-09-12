import json
import logging
import requests
requests.packages.urllib3.disable_warnings() 
import backoff
import jsonpath_ng
import os
from typing import List, Union
from jsonpath_ng.exceptions import JsonPathParserError


from garak import _config
from garak.generators.base import Generator
from garak.exception import APIKeyMissingError, RateLimitHit


class MultiEndpointGenerator(Generator):
    """A REST generator that sends a POST request and retrieves the response with a subsequent GET request.
    Example configuration json;
    {
        "multi_endpoint_rest": {
            "MultiEndpointGenerator": {
                "name": "example service",
                "post_uri": "https://example.ai/llm",
                "post_headers": {
                    "X-Authorization": "$KEY"
                },
                "post_req_template_json_object": {
                    "text": "$INPUT"
                },
                "post_response_json": true,
                "post_response_json_field": "job_id",
                "get_uri": "https://example.ai/llm",
                "get_headers": {
                    "X-Authorization": "$KEY"
                },
                "get_req_template_json_object": {
                    "text": "$INPUT"
                },
                "post_response_json": true,
                "post_response_json_field": "text"
            }
        }
    }
    """

    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "first_stage_uri": "https://localhost",
        "first_stage_method": "post",
        "first_stage_headers": {},
        "first_stage_req_template": "$INPUT",
        "first_stage_response_json": False,
        "first_stage_required_returns": None,
        "second_stage_uri": "https://localhost",
        "second_stage_method": "get",
        "second_stage_headers": {},
        "second_stage_req_template": "$INPUT",
        "second_stage_response_json": False,
        "second_stage_response_json_field": None,
        "second_stage_req_template_json_object": None,
        "ratelimit_codes": [429],
        "request_timeout": 20,
        "proxies": None,
        "verify_ssl": True,
    }

    generator_family_name = "MultiEndpointREST"

    _supported_params = (
        "key_env_var",
        "token_refresh_vars",
        "first_stage_uri",
        "first_stage_method",
        "first_stage_headers",
        "first_stage_req_template",
        "first_stage_req_template_json_object",
        "first_stage_response_json",
        "first_stage_required_returns",
        "second_stage_uri",
        "second_stage_method",
        "second_stage_headers",
        "second_stage_req_template",
        "second_stage_req_template_json_object",
        "second_stage_response_json",
        "second_stage_response_json_field",
        "api_key",
        "name",
        "proxies",
        "verify_ssl",
        "ratelimit_codes",
        "request_timeout",
        "max_tokens",
        "temperature",
        "top_k",
        "context_len"
    )

    def __init__(self, config_root=_config):
        # Set up the self object
        self.need_token_refresh = False
        self.key_env_var = self.ENV_VAR if hasattr(self, "ENV_VAR") else None

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

        
        # Load the first stage request template
        if (hasattr(self, "first_stage_req_template_json_object") and self.first_stage_req_template_json_object is not None):
            self.first_stage_req_template = json.dumps(
                self.first_stage_req_template_json_object)

        # Validate configuration for first stage
        if self.first_stage_response_json:
            if self.first_stage_required_returns is None:
                raise ValueError(
                    "MultiEndpointGenerator first_stage_response_json is True but first_stage_required_returns isn't set"
                )
            if not isinstance(self.first_stage_required_returns, list):
                raise ValueError(
                    "first_stage_required_returns must be a list")
            if self.first_stage_required_returns == []:
                raise ValueError(
                    "MultiEndpointGenerator first_stage_response_json is True but first_stage_required_returns is an empty list. If the root object is the target object, use a JSONPath."
                )
        # Validate configuration for second stage
        if self.second_stage_response_json:
            if self.second_stage_response_json_field is None:
                raise ValueError(
                    "MultiEndpointGenerator second_stage_response_json is True but second_stage_response_json_field isn't set"
                )
            if not isinstance(self.second_stage_response_json_field, str):
                raise ValueError(
                    "second_stage_response_json_field must be a string")
            if self.second_stage_response_json_field == "":
                raise ValueError(
                    "MultiEndpointGenerator second_stage_response_json is True but second_stage_response_json_field is an empty string. If the root object is the target object, use a JSONPath."
                )
        # Ensure that the object has a name (used in logging)
        if self.name is None:
            self.name = self.first_stage_uri + " -> " + self.second_stage_uri

        if self.first_stage_uri is None or self.second_stage_uri is None:
            raise ValueError(
                "No REST endpoint URI definition found in either constructor param, JSON, or --model_name. Please specify one."
            )

        self.fullname = f"{self.generator_family_name} {self.name}"
        self.first_stage_method = self.first_stage_method.lower()
        self.second_stage_method = self.second_stage_method.lower()

        valid_methods = ["get", "post", "put",
                         "patch", "options", "delete", "head"]
        if self.first_stage_method not in valid_methods or self.second_stage_method not in valid_methods:
            logging.info(
                "RestGenerator HTTP method %s or %s not supported, defaulting to 'post'",
                self.first_stage_method, self.second_stage_method
            )

        self.first_stage_http_function = getattr(
            requests, self.first_stage_method)
        self.second_stage_http_function = getattr(
            requests, self.second_stage_method)

        # validate jsonpath
        if self.first_stage_response_json and self.first_stage_required_returns or self.second_stage_response_json and self.second_stage_response_json_field:
            for required_return in self.first_stage_required_returns:
                try:
                    tmp = jsonpath_ng.parse(required_return["json_field"])
                except JsonPathParserError as e:
                    logging.CRITICAL(f"Couldn't parse {required_return['name']} json_field: {required_return['json_field']}"
                                     )
                    raise e

            try:
                self.second_stage_json_expr = jsonpath_ng.parse(
                    self.second_stage_response_json_field)
            except JsonPathParserError as e:
                logging.CRITICAL(
                    "Couldn't parse second_stage_response_json_field: %s", self.second_stage_response_json_field
                )
                raise e

        super().__init__(self.name, config_root=config_root)

    def _validate_env_var(self):
        key_match = "$KEY"
        header_requires_key = False
        for _k, v in self.first_stage_headers.items():
            if key_match in v:
                header_requires_key = True
        for _k, v in self.second_stage_headers.items():
            if key_match in v:
                header_requires_key = True

        # loads the key_env_var (OPENAI_API_KEY) from the environment into self.api_key
        if "$KEY" in self.first_stage_req_template or "$KEY" in self.second_stage_req_template or header_requires_key:
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
                output = output.replace(
                    "$KEY", self._json_escape(self.api_key))
            else:
                output = output.replace("$KEY", self.api_key)
        return output.replace("$INPUT", self._json_escape(text))

    def _populate_second_stage(self, required_returns: list):
        for required_return in required_returns:
            if required_return["name"] in self.second_stage_uri:
                self.second_stage_uri = self.second_stage_uri.replace(
                    required_return["name"], required_return["value"])

    def _populate_token_refresh(self, token_refresh_request_data: dict) -> dict:
        for key in token_refresh_request_data:
            placeholder = token_refresh_request_data[key].strip('{}').upper()
            if placeholder in self.token_refresh_config['secrets']:
                token_refresh_request_data[key] = self.token_refresh_config['secrets'][placeholder]
        return token_refresh_request_data        


    @backoff.on_exception(backoff.fibo, RateLimitHit, max_value=70)
    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        """Send a POST request and retrieve the response with a subsequent GET request."""

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





        # Populate first stage request body
        first_stage_request_data = self._populate_template(self.first_stage_req_template, prompt)

        # Populate first stage request headers
        first_stage_request_headers = dict(self.first_stage_headers)

        # Populate placeholders in the first stage headers
        for k, v in self.first_stage_headers.items():
            first_stage_request_headers[k] = self._populate_template(v, prompt)

        first_stage_data_kw = "params" if self.first_stage_http_function == requests.get else "data"
        second_stage_data_kw = "params" if self.second_stage_http_function == requests.get else "data"

        first_stage_req_kArgs = {
            first_stage_data_kw: first_stage_request_data,
            "headers": first_stage_request_headers,
            "timeout": self.request_timeout,
            "proxies": self.proxies,
            "verify": self.verify_ssl,
        }

        first_stage_resp = self.first_stage_http_function(self.first_stage_uri, **first_stage_req_kArgs)

        if first_stage_resp.status_code in self.ratelimit_codes:
            raise RateLimitHit(
                f"Rate limited: {first_stage_resp.status_code} - {first_stage_resp.reason}")

        elif str(first_stage_resp.status_code)[0] == "3":
            raise NotImplementedError(
                f"REST URI redirection: {first_stage_resp.status_code} - {first_stage_resp.reason}"
            )

        elif str(first_stage_resp.status_code)[0] == "4":
            # Token is expired, refresh it
            if first_stage_resp.status_code == 401:
                self.need_token_refresh = True
                raise RateLimitHit(
                    f"Rate limited: {first_stage_resp.status_code} - {first_stage_resp.reason}")
            else:
                raise ConnectionError(
                f"REST URI client error: {first_stage_resp.status_code} - {first_stage_resp.reason}"
            )



        elif str(first_stage_resp.status_code)[0] == "5":
            error_msg = f"REST URI server error: {first_stage_resp.status_code} - {first_stage_resp.reason}"
            if self.retry_5xx:
                raise IOError(error_msg)
            else:
                raise ConnectionError(error_msg)

        first_stage_response_object = json.loads(first_stage_resp.content)

        # Validation assertions
        assert (self.first_stage_response_json), "response_json must be True at this point; if False, we should have returned already"
        assert isinstance(self.first_stage_required_returns,
                          list), "first_stage_required_returns must be a list"
        assert (len(self.first_stage_required_returns) >
                0), "first_stage_required_returns needs to be complete if first_stage_response_json is true; ValueError should have been raised in constructor"

        response_fields = []
        for required_return in self.first_stage_required_returns:
            field_path_expr = jsonpath_ng.parse(required_return["json_field"])
            tmp_output_var = field_path_expr.find(first_stage_response_object)
            if len(tmp_output_var) == 1:
                tmp = {
                    "name": required_return["name"],
                    "value": tmp_output_var[0].value
                }
                response_fields.append(tmp)
            else:
                logging.error(
                    "RestGenerator JSONPath in first_stage_required_returns yielded nothing. Response content: %s"
                    % repr(first_stage_response_object)
                )

        # Populate second stage request body with the first stage response fields
        self._populate_second_stage(response_fields)
        second_stage_request_data = self._populate_template(self.second_stage_req_template, prompt)
        # Populate second stage request headers
        second_stage_request_headers = dict(self.second_stage_headers)
        # Populate placeholders in the second stage headers
        for k, v in self.second_stage_headers.items():
            second_stage_request_headers[k] = self._populate_template(
                v, prompt)

        second_stage_req_kArgs = {
            second_stage_data_kw: second_stage_request_data,
            "headers": second_stage_request_headers,
            "timeout": self.request_timeout,
            "proxies": self.proxies,
            "verify": self.verify_ssl,
        }

        second_stage_resp = self.second_stage_http_function(self.second_stage_uri, **second_stage_req_kArgs)


        if second_stage_resp.status_code in self.ratelimit_codes:
            raise RateLimitHit(
                f"Rate limited: {second_stage_resp.status_code} - {second_stage_resp.reason}")

        elif str(second_stage_resp.status_code)[0] == "3":
            raise NotImplementedError(
                f"REST URI redirection: {second_stage_resp.status_code} - {second_stage_resp.reason}"
            )

        elif str(second_stage_resp.status_code)[0] == "4":
            # Token is expired, refresh it
            if first_stage_resp.status_code == 401:
                self.need_token_refresh = True
                raise RateLimitHit(
                    f"Rate limited: {first_stage_resp.status_code} - {first_stage_resp.reason}")
            else:
                raise ConnectionError(
                f"REST URI client error: {first_stage_resp.status_code} - {first_stage_resp.reason}"
            )

        elif str(second_stage_resp.status_code)[0] == "5":
            error_msg = f"REST URI server error: {second_stage_resp.status_code} - {second_stage_resp.reason}"
            if self.retry_5xx:
                raise IOError(error_msg)
            else:
                raise ConnectionError(error_msg)

        second_stage_response_object = json.loads(second_stage_resp.content)


        # if response_json_field starts with a $, treat is as a JSONPath
        assert (self.second_stage_response_json), "second_stage_response_json must be True at this point; if False, we should have returned already"
        assert isinstance(self.second_stage_response_json_field,str), "second_stage_response_json_field must be a string"
        assert (len(self.second_stage_response_json_field) >0), "second_stage_response_json_field needs to be complete if second_stage_response_json is true; ValueError should have been raised in constructor"
        if self.second_stage_response_json_field[0] != "$":
            second_stage_json_extraction_result = [
                second_stage_response_object[self.second_stage_response_json_field]]
        else:
            field_path_expr = jsonpath_ng.parse(self.second_stage_response_json_field)
            second_stage_json_extraction_results = field_path_expr.find(second_stage_response_object)
            if len(second_stage_json_extraction_results) == 1:
                response_value = second_stage_json_extraction_results[0].value
                if isinstance(response_value, str):
                    second_stage_json_extraction_result = [response_value]
                elif isinstance(response_value, list):
                    second_stage_json_extraction_result = response_value
            elif len(second_stage_json_extraction_results) > 1:
                second_stage_json_extraction_result = [
                    r.value for r in second_stage_json_extraction_results]
            else:
                logging.error(
                    "MultiEndpointGenerator JSONPath in response_json_field yielded nothing. Response content: %s"
                    % repr(second_stage_response_object)
                )
                return [None]

        return second_stage_json_extraction_result

        ################################################################################

        job_id = self.prompt_sender._call_model(prompt, generations_this_call)
        self.response_retriever.uri = f"{self.get_uri}/{job_id}"
        return self.response_retriever._call_model(job_id, generations_this_call)


DEFAULT_CLASS = "MultiEndpointGenerator"
