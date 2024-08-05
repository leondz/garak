import os
import pytest

import garak.cli
from garak.generators.azure import AzureOpenAIChat

DEFAULT_GENERATIONS_QTY = 10

@pytest.mark.skipif(
    os.getenv("AZURE_DEPLOYMENT_NAME", None) is None,
    reason=f"AZURE_DEPLOYMENT_NAME env variable is not set",
)

@pytest.mark.skipif(
    os.getenv("AZURE_ENDPOINT", None) is None,
    reason=f"AZURE_ENDPOINT env variable is not set",
)

@pytest.mark.skipif(
    os.getenv(AzureOpenAIChat.ENV_VAR, None) is None,
    reason=f"Azure OpenAI API key is not set in {AzureOpenAIChat.ENV_VAR}",
)

def test_openai_chat():
    generator = AzureOpenAIChat(name="gpt-4o")
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
