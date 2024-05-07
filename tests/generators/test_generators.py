# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak.generators.test import Blank, Repeat, Single

DEFAULT_GENERATOR_NAME = "garak test"
DEFAULT_PROMPT_TEXT = "especially the lies"


def test_generators_test_blank():
    g = Blank(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=5)
    assert output == [
        "",
        "",
        "",
        "",
        "",
    ], "generators.test.Blank with generations=5 should return five empty strings"


def test_generators_test_repeat():
    g = Repeat(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt=DEFAULT_PROMPT_TEXT, generations_this_call=1)
    assert output == [
        DEFAULT_PROMPT_TEXT
    ], "generators.test.Repeat should send back a list of the posed prompt string"


def test_generators_test_single_one():
    g = Single(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=1)
    assert isinstance(
        output, list
    ), "Single generator .generate() should send back a list"
    assert (
        len(output) == 1
    ), "Single.generate() with generations = 1 should send a list of one string"
    assert isinstance(
        output[0], str
    ), "Single generator output list should contain strings"

    output = g._call_model(prompt="test", generations_this_call=1)
    assert isinstance(output, list), "Single generator _call_model should return a list"
    assert (
        len(output) == 1
    ), "_call_model w/ generations_this_call 1 should return a list of length 1"
    assert isinstance(
        output[0], str
    ), "Single generator output list should contain strings"


def test_generators_test_single_many():
    g = Single(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=2)
    assert isinstance(
        output, list
    ), "Single generator .generate() should send back a list"
    assert (
        len(output) == 2
    ), "Single.generate() with generations = 2 should send a list of length 2"
    assert isinstance(
        output[0], str
    ), "Single generator output list should contain strings (first position)"
    assert isinstance(
        output[1], str
    ), "Single generator output list should contain strings (second position)"


def test_generators_test_single_too_many():
    g = Single(DEFAULT_GENERATOR_NAME)
    with pytest.raises(ValueError):
        output = g._call_model(prompt="test", generations_this_call=2)
    assert "Single._call_model should refuse to process generations_this_call > 1"


def test_generators_test_blank_one():
    g = Blank(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=1)
    assert isinstance(
        output, list
    ), "Blank generator .generate() should send back a list"
    assert (
        len(output) == 1
    ), "Blank generator .generate() w/ generations=1 should return a list of length 1"
    assert isinstance(
        output[0], str
    ), "Blank generator output list should contain strings"
    assert (
        output[0] == ""
    ), "Blank generator .generate() output list should contain strings"


def test_generators_test_blank_many():
    g = Blank(DEFAULT_GENERATOR_NAME)
    output = g.generate(prompt="test", generations_this_call=2)
    assert isinstance(
        output, list
    ), "Blank generator .generate() should send back a list"
    assert (
        len(output) == 2
    ), "Blank generator .generate() w/ generations=2 should return a list of length 2"
    assert isinstance(
        output[0], str
    ), "Blank generator output list should contain strings (first position)"
    assert isinstance(
        output[1], str
    ), "Blank generator output list should contain strings (second position)"
    assert (
        output[0] == ""
    ), "Blank generator .generate() output list should contain strings (first position)"
    assert (
        output[1] == ""
    ), "Blank generator .generate() output list should contain strings (second position)"
