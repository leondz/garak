# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak.generators.test import Blank, Repeat, Single

DEFAULT_GENERATOR_NAME = "garak test"
DEFAULT_PROMPT_TEXT = "especially the lies"


def test_generators_test_blank():
    g = Blank(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=5)
    assert output == ["", "", "", "", ""]


def test_generators_test_repeat():
    g = Repeat(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt=DEFAULT_PROMPT_TEXT, generations_this_call=1)
    assert output == [DEFAULT_PROMPT_TEXT]


def test_generators_test_single_one():
    g = Single(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=1)
    assert isinstance(output, list)
    assert len(output) == 1
    assert isinstance(output[0], str)


def test_generators_test_single_many():
    g = Single(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=2)
    assert isinstance(output, list)
    assert len(output) == 2
    assert isinstance(output[0], str)
    assert isinstance(output[1], str)


def test_generators_test_single_too_many():
    g = Single(DEFAULT_GENERATOR_NAME)
    with pytest.raises(ValueError):
        output = g._call_model(prompt="test", generations_this_call=2)
