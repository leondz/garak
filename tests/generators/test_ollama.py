import pytest
import ollama
from httpx import ConnectError
from garak.generators.ollama import OllamaGeneratorChat

PINGED_OLLAMA_SERVER = False # Avoid calling the server multiple times if it is not running
OLLAMA_SERVER_UP = False

def ollama_is_running():
    global PINGED_OLLAMA_SERVER
    global OLLAMA_SERVER_UP

    if not PINGED_OLLAMA_SERVER:
        try:
            ollama.list() # Gets a list of all pulled models. Used as a ping
            OLLAMA_SERVER_UP = True
        except ConnectError:
            OLLAMA_SERVER_UP = False
        finally:
            PINGED_OLLAMA_SERVER = True
    return OLLAMA_SERVER_UP


@pytest.mark.skipif(
    not ollama_is_running(),
    reason=f"Ollama server is not currently running",
)
def test_error_on_nonexistant_model():
    model_name = "non-existant-model"
    gen = OllamaGeneratorChat(model_name)
    with pytest.raises(ollama.ResponseError):
        gen.generate("This shouldnt work")


@pytest.mark.skipif(
    not ollama_is_running(),
    reason=f"Ollama server is not currently running",
)
@pytest.mark.skipif(
    not ollama_is_running() or len(ollama.list()) == 0 or len(ollama.list()["models"]) == 0,
    reason=f"No Ollama models pulled"
)
# This test might fail if the GPU is busy, and the generation takes more than 30 seconds
def test_generation_on_pulled_model():
    model_name = ollama.list()["models"][0]["name"]
    gen = OllamaGeneratorChat(model_name)
    responses = gen.generate("Say \"Hello!\"")
    assert len(responses) == gen.generations
    assert all(isinstance(response, str) for response in responses)
    assert all(len(response) > 0 for response in responses)