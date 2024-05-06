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
    result = g._call_model("this is a test", generations_this_call=1)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], str)


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
