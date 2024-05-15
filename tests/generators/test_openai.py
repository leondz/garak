# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import httpx
import respx
import pytest

import openai

from garak.generators.openai import OpenAIGenerator

DEFAULT_GENERATIONS_QTY = 10


@pytest.fixture
def set_fake_env() -> None:
    os.environ[OpenAIGenerator.ENV_VAR] = "invalid_api_key"


# helper method to pass mock config
def generate_in_subprocess(*args):
    generator, mock_response, prompt = args[0]
    print("completed a result")
    with respx.mock(
        base_url="https://api.openai.com/v1", assert_all_called=False
    ) as respx_mock:
        respx_mock.post("/completions").mock(
            return_value=httpx.Response(
                mock_response["code"], json=mock_response["json"]
            )
        )
        return generator.generate(prompt)


def test_openai_version():
    assert openai.__version__.split(".")[0] == "1"  # expect openai module v1.x


@pytest.mark.usefixtures("set_fake_env")
def test_openai_multiprocessing(openai_compat_mocks):
    parallel_attempts = 4
    generator = OpenAIGenerator(name="gpt-3.5-turbo-instruct")
    prompt_sets = [
        [
            (generator, openai_compat_mocks.completion, "first testing string"),
            (generator, openai_compat_mocks.completion, "second testing string"),
            (generator, openai_compat_mocks.completion, "third testing string"),
        ],
        [
            (generator, openai_compat_mocks.completion, "fourth testing string"),
            (generator, openai_compat_mocks.completion, "firth testing string"),
            (generator, openai_compat_mocks.completion, "sixth testing string"),
        ],
    ]

    for prompts in prompt_sets:
        from multiprocessing import Pool

        with Pool(parallel_attempts) as attempt_pool:
            for result in attempt_pool.imap_unordered(generate_in_subprocess, prompts):
                print("completed a result")
                assert result is not None


@pytest.mark.usefixtures("set_fake_env")
@pytest.mark.respx(base_url="https://api.openai.com/v1")
def test_openai_invalid_model_names(respx_mock, openai_compat_mocks):
    mock_resp = openai_compat_mocks.models
    respx_mock.get("/models").mock(
        return_value=httpx.Response(mock_resp["code"], json=mock_resp["json"])
    )
    with pytest.raises(ValueError) as e_info:
        generator = OpenAIGenerator(name="")
    assert "name is required for" in str(e_info.value)
    with pytest.raises(ValueError) as e_info:
        generator = OpenAIGenerator(name="this is not a real model name")
    assert "please add one!" in str(e_info.value)


@pytest.mark.skipif(
    os.getenv(OpenAIGenerator.ENV_VAR, None) is None,
    reason=f"OpenAI API key is not set in {OpenAIGenerator.ENV_VAR}",
)
def test_openai_completion():
    generator = OpenAIGenerator(name="gpt-3.5-turbo-instruct")
    assert generator.name == "gpt-3.5-turbo-instruct"
    assert generator.generations == DEFAULT_GENERATIONS_QTY
    assert isinstance(generator.max_tokens, int)
    generator.max_tokens = 99
    assert generator.max_tokens == 99
    generator.temperature = 0.5
    assert generator.temperature == 0.5
    output = generator.generate("How could I possibly ")
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)
    print("test passed!")


@pytest.mark.skipif(
    os.getenv(OpenAIGenerator.ENV_VAR, None) is None,
    reason=f"OpenAI API key is not set in {OpenAIGenerator.ENV_VAR}",
)
def test_openai_chat():
    generator = OpenAIGenerator(name="gpt-3.5-turbo")
    assert generator.name == "gpt-3.5-turbo"
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
