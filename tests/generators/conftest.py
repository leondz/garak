import json
import pytest
import pathlib


@pytest.fixture
def openai_compat_mocks():
    """Mock responses for OpenAI compatible endpoints"""
    with open(pathlib.Path(__file__).parents[0] / "openai.json") as mock_openai:
        return json.load(mock_openai)
