# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

import garak.cli
from garak.generators.groq import GroqChat


@pytest.mark.skipif(
    os.getenv(GroqChat.ENV_VAR, None) is None,
    reason=f"GroqChat API key is not set in {GroqChat.ENV_VAR}",
)
def test_groq_instantiate():
    g = GroqChat(name="llama3-8b-8192")


@pytest.mark.skipif(
    os.getenv(GroqChat.ENV_VAR, None) is None,
    reason=f"GroqChat  API key is not set in {GroqChat.ENV_VAR}",
)
def test_groq_generate_1():
    g = GroqChat(name="llama3-8b-8192")
    result = g._call_model("this is a test", generations_this_call=1)
    assert isinstance(result, list), "GroqChat _call_model should return a list"
    assert len(result) == 1, "GroqChat _call_model result list should have one item"
    assert isinstance(result[0], str), "GroqChat _call_model should return a list"
    result = g.generate("this is a test", generations_this_call=1)
    assert isinstance(result, list), "GroqChat generate() should return a list"
    assert (
        len(result) == 1
    ), "GroqChat generate() result list should have one item when generations_this_call=1"
    assert isinstance(result[0], str), "GroqChat generate() should return a list"
