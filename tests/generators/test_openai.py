# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

import openai

from garak.generators.openai import OpenAIGenerator

DEFAULT_GENERATIONS_QTY = 10


def test_openai_version():
    assert openai.__version__.split(".")[0] == "1"  # expect openai module v1.x


@pytest.mark.skipif(
    os.getenv("OPENAI_API_KEY", None) is None,
    reason="OpenAI API key is not set in OPENAI_API_KEY",
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
    os.getenv("OPENAI_API_KEY", None) is None,
    reason="OpenAI API key is not set in OPENAI_API_KEY",
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
