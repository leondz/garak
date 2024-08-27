import pytest

from os import getenv

from garak.generators.litellm import LiteLLMGenerator


@pytest.mark.skipif(
    getenv("OPENAI_API_KEY", None) is None,
    reason="OpenAI API key is not set in OPENAI_API_KEY",
)
def test_litellm_openai():
    model_name = "gpt-3.5-turbo"
    generator = LiteLLMGenerator(name=model_name)
    assert generator.name == model_name
    assert isinstance(generator.max_tokens, int)

    output = generator.generate("How do I write a sonnet?")
    assert len(output) == 1  # expect 1 generation by default

    for item in output:
        assert isinstance(item, str)
    print("test passed!")


@pytest.mark.skipif(
    getenv("OPENROUTER_API_KEY", None) is None,
    reason="OpenRouter API key is not set in OPENROUTER_API_KEY",
)
def test_litellm_openrouter():
    model_name = "openrouter/google/gemma-7b-it"
    generator = LiteLLMGenerator(name=model_name)
    assert generator.name == model_name
    assert isinstance(generator.max_tokens, int)

    output = generator.generate("How do I write a sonnet?")
    assert len(output) == 1  # expect 1 generation by default

    for item in output:
        assert isinstance(item, str)
    print("test passed!")
