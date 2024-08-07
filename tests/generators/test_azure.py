import os
import pytest

from garak.generators.azure import AzureOpenAIGenerator

DEFAULT_GENERATIONS_QTY = 10


def test_azureopenai_invalid_model_names():
    with pytest.raises(ValueError) as e_info:
        generator = AzureOpenAIGenerator(name="")
    assert "name is required for" in str(e_info.value)
    with pytest.raises(ValueError) as e_info:
        generator = AzureOpenAIGenerator(name="this is not a real model name")
    assert "please add one!" in str(e_info.value)

@pytest.mark.skipif(
    os.getenv(AzureOpenAIGenerator.ENV_VAR, None) is None,
    reason=f"OpenAI API key is not set in {AzureOpenAIGenerator.ENV_VAR}",
)
@pytest.mark.skipif(
    os.getenv(AzureOpenAIGenerator.DEPLOYMENT_NAME_ENV_VAR, None) is None,
    reason=f"Deployment name is not set in {AzureOpenAIGenerator.DEPLOYMENT_NAME_ENV_VAR}",
)
@pytest.mark.skipif(
    os.getenv(AzureOpenAIGenerator.ENDPOINT_ENV_VAR, None) is None,
    reason=f"Azure endpoint is not set in {AzureOpenAIGenerator.ENDPOINT_ENV_VAR}",
)
def test_azureopenai_chat():
    generator = AzureOpenAIGenerator(name="gpt-4o")
    assert generator.name == "gpt-4o"
    assert generator.name_backup == "gpt-4o" 
    assert generator.generations == DEFAULT_GENERATIONS_QTY
    assert isinstance(generator.max_tokens, int)
    generator.max_tokens = 99
    assert generator.max_tokens == 99
    generator.temperature = 0.5
    assert generator.temperature == 0.5
    output = generator.generate("Hello OpenAI!")
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)
    messages = [
        {"role": "user", "content": "Hello OpenAI!"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "How do I write a sonnet?"},
    ]
    output = generator.generate(messages)
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)
    print("test passed!")
