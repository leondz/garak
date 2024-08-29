import pytest
import ollama
from garak.generators.ollama import OllamaGeneratorChat

# TODO: Check if any Ollama server is currently running, and if not skip the tests

def test_error_on_nonexistant_model():
    model_name = "non-existant-model"
    gen = OllamaGeneratorChat(model_name)
    with pytest.raises(ollama.ResponseError):
        gen.generate("This shouldnt work")
