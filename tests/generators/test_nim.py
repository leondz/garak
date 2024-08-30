# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest

import garak.cli
from garak.generators.nim import NVOpenAIChat


@pytest.mark.skipif(
    os.getenv(NVOpenAIChat.ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NVOpenAIChat.ENV_VAR}",
)
def test_nim_instantiate():
    g = NVOpenAIChat(name="google/gemma-2b")


@pytest.mark.skipif(
    os.getenv(NVOpenAIChat.ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NVOpenAIChat.ENV_VAR}",
)
def test_nim_generate_1():
    g = NVOpenAIChat(name="google/gemma-2b")
    result = g._call_model("this is a test")
    assert isinstance(result, list), "NIM _call_model should return a list"
    assert len(result) == 1, "NIM _call_model result list should have one item"
    assert isinstance(result[0], str), "NIM _call_model should return a list"
    result = g.generate("this is a test")
    assert isinstance(result, list), "NIM generate() should return a list"
    assert (
        len(result) == 1
    ), "NIM generate() result list should have one item using default generations_this_call"
    assert isinstance(result[0], str), "NIM generate() should return a list"


@pytest.mark.skipif(
    os.getenv(NVOpenAIChat.ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NVOpenAIChat.ENV_VAR}",
)
def test_nim_parallel_attempts():
    garak.cli.main(
        "-m nim -p lmrc.Anthropomorphisation -g 1 -n google/gemma-2b --parallel_attempts 10".split()
    )
    assert True


@pytest.mark.skipif(
    os.getenv(NVOpenAIChat.ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NVOpenAIChat.ENV_VAR}",
)
def test_nim_hf_detector():
    garak.cli.main("-m nim -p lmrc.Bullying -g 1 -n google/gemma-2b".split())
    assert True


@pytest.mark.skipif(
    os.getenv(NVOpenAIChat.ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NVOpenAIChat.ENV_VAR}",
)
def test_nim_conservative_api():  # extraneous params can throw 422
    g = NVOpenAIChat(name="nvidia/nemotron-4-340b-instruct")
    result = g._call_model("this is a test")
    assert isinstance(result, list), "NIM _call_model should return a list"
    assert len(result) == 1, "NIM _call_model result list should have one item"
    assert isinstance(result[0], str), "NIM _call_model should return a list"
    result = g.generate("this is a test")
    assert isinstance(result, list), "NIM generate() should return a list"
    assert (
        len(result) == 1
    ), "NIM generate() result list should have one item using default generations_this_call"
    assert isinstance(result[0], str), "NIM generate() should return a list"
