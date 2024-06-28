import json
import pytest
import requests_mock
from sympy import is_increasing

from garak import _config

from garak.generators.rest import RestGenerator

DEFAULT_GENERATIONS_QTY = 11
DEFAULT_NAME = "REST Test"
DEFAULT_URI = "https://www.wikidata.org/wiki/Q22971"
DEFAULT_TEXT_RESPONSE = "Here's your model response"


@pytest.fixture
def set_rest_config():
    _config.plugins.generators["rest"] = {}
    _config.plugins.generators["rest"]["RestGenerator"] = {
        "name": DEFAULT_NAME,
        "uri": DEFAULT_URI,
        "api_key": "testing",
        "generations": DEFAULT_GENERATIONS_QTY,
    }
    # excluded: req_template_json_object, response_json_field


@pytest.mark.usefixtures("set_rest_config")
def test_rest_generator_initialization():
    generator = RestGenerator()
    assert generator.generations == DEFAULT_GENERATIONS_QTY
    assert generator.name == DEFAULT_NAME
    assert generator.uri == DEFAULT_URI


# plain text test
@pytest.mark.usefixtures("set_rest_config")
def test_plaintext_rest(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=DEFAULT_TEXT_RESPONSE,
    )
    generator = RestGenerator()
    output = generator._call_model("sup REST")
    assert output == [DEFAULT_TEXT_RESPONSE]


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_top_level(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps({"text": DEFAULT_TEXT_RESPONSE}),
    )
    _config.plugins.generators["rest"]["RestGenerator"]["response_json"] = True
    _config.plugins.generators["rest"]["RestGenerator"]["response_json_field"] = "text"
    generator = RestGenerator()
    print(generator.response_json)
    print(generator.response_json_field)
    output = generator._call_model("Who is Enabran Tain's son?")
    assert output == [DEFAULT_TEXT_RESPONSE]


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_list(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps([DEFAULT_TEXT_RESPONSE] * DEFAULT_GENERATIONS_QTY),
    )
    _config.plugins.generators["rest"]["RestGenerator"]["response_json"] = True
    _config.plugins.generators["rest"]["RestGenerator"]["response_json_field"] = "$"
    generator = RestGenerator()
    output = generator._call_model("Who is Enabran Tain's son?")
    assert output == [DEFAULT_TEXT_RESPONSE] * DEFAULT_GENERATIONS_QTY


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_deeper(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": DEFAULT_TEXT_RESPONSE,
                        },
                    }
                ]
            }
        ),
    )
    _config.plugins.generators["rest"]["RestGenerator"]["response_json"] = True
    _config.plugins.generators["rest"]["RestGenerator"][
        "response_json_field"
    ] = "$.choices[*].message.content"
    generator = RestGenerator()
    output = generator._call_model("Who is Enabran Tain's son?")
    assert output == [DEFAULT_TEXT_RESPONSE]
