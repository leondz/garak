import os
import pytest
import requests_mock
from sympy import is_increasing

from garak import _config

from garak.generators.rest import RestGenerator

DEFAULT_GENERATIONS_QTY = 10
DEFAULT_NAME = "REST Test"
DEFAULT_URI = "https://www.wikidata.org/wiki/Q22971"
DEFAULT_RESPONSE = "Here's your model response"


@pytest.fixture
def set_rest_config():
    _config.plugins.generators["rest.RestGenerator"] = {
        "name": DEFAULT_NAME,
        "uri": DEFAULT_URI,
    }
    # excluded: req_template_json_object, response_json_field


@pytest.mark.usefixtures("set_rest_config")
def test_langchain_serve_generator_initialization():
    generator = RestGenerator()
    assert generator.generations == DEFAULT_GENERATIONS_QTY
    assert generator.name == DEFAULT_NAME
    assert generator.uri == DEFAULT_URI


# plain text test
@pytest.mark.usefixtures("set_rest_config")
def test_plaintext_rest(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=DEFAULT_RESPONSE,
    )
    generator = RestGenerator()
    output = generator._call_model("sup REST")
    print("o", repr(output))
    print("d", repr(DEFAULT_RESPONSE))
    assert output == DEFAULT_RESPONSE


# dict access test

# JSONPath test
