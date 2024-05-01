# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import contextlib
import json
import os
import pytest

import garak.attempt
import garak.cli


def test_attempt_sticky_params(capsys):
    garak.cli.main(
        "-m test.Blank -g 1 -p atkgen,dan.Dan_6_0 --report_prefix _garak_test_attempt_sticky_params".split()
    )
    reportlines = (
        open("_garak_test_attempt_sticky_params.report.jsonl", "r", encoding="utf-8")
        .read()
        .split("\n")
    )
    complete_atkgen = json.loads(reportlines[3])  # status 2 for the one atkgen attempt
    complete_dan = json.loads(reportlines[6])  # status 2 for the one dan attempt
    assert complete_atkgen["notes"] != {}
    assert complete_dan["notes"] == {}
    assert complete_atkgen["notes"] != complete_dan["notes"]


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""

    def remove_reports():
        with contextlib.suppress(FileNotFoundError):
            os.remove("_garak_test_attempt_sticky_params.report.jsonl")
            os.remove("_garak_test_attempt_sticky_params.report.html")
            os.remove("_garak_test_attempt_sticky_params.hitlog.jsonl")

    request.addfinalizer(remove_reports)


def test_turn_taking():
    a = garak.attempt.Attempt()
    assert a.messages == [], "Newly constructed attempt should have no message history"
    assert a.outputs == [], "Newly constructed attempt should have empty outputs"
    assert a.prompt is None, "Newly constructed attempt should have no prompt"
    first_prompt = "what is up"
    a.prompt = first_prompt
    assert (
        a.prompt == first_prompt
    ), "Setting attempt.prompt on new prompt should lead to attempt.prompt returning that prompt string"
    assert a.messages == [{"role": "user", "content": first_prompt}]
    assert a.outputs == []
    first_response = ["not much", "as an ai"]
    a.outputs = first_response
    assert a.prompt == first_prompt
    assert a.messages == [
        [
            {"role": "user", "content": first_prompt},
            {"role": "assistant", "content": first_response[0]},
        ],
        [
            {"role": "user", "content": first_prompt},
            {"role": "assistant", "content": first_response[1]},
        ],
    ]
    assert a.outputs == first_response


def test_history_lengths():
    a = garak.attempt.Attempt()
    a.prompt = "sup"
    assert len(a.messages) == 1, "Attempt with one prompt should have one history"
    generations = 4
    a.outputs = ["x"] * generations
    assert len(a.messages) == generations, "Attempt should expand history automatically"
    with pytest.raises(ValueError):
        a.outputs = ["x"] * (generations - 1)
    with pytest.raises(ValueError):
        a.outputs = ["x"] * (generations + 1)
    new_prompt_text = "y"
    a.latest_prompts = [new_prompt_text] * generations
    assert len(a.messages) == generations, "History should track all generations"
    assert len(a.messages[0]) == 3, "Three turns so far"
    assert (
        len(a.latest_prompts) == generations
    ), "Should be correct number of latest prompts"
    assert (
        a.latest_prompts[0] == new_prompt_text
    ), "latest_prompts should be tracking latest addition"


def test_illegal_ops():
    a = garak.attempt.Attempt()
    with pytest.raises(ValueError):
        a.latest_prompts = [
            "a"
        ]  # shouldn't be able to set latest_prompts until the generations count is known, from outputs()

    a = garak.attempt.Attempt()
    a.prompt = "prompts"
    with pytest.raises(ValueError):
        a.latest_prompts = [
            "a"
        ]  # shouldn't be able to set latest_prompts until the generations count is known, from outputs()

    a = garak.attempt.Attempt()
    a.prompt = "prompt"
    with pytest.raises(ValueError):
        a.prompt = "shouldn't be able to set initial prompt twice"

    a = garak.attempt.Attempt()
    a.prompt = "prompt"
    a.outputs = ["output"]
    with pytest.raises(ValueError):
        a.prompt = "shouldn't be able to set initial prompt after output turned up"

    a = garak.attempt.Attempt()
    a.prompt = "prompt"
    a.outputs = ["output"]
    with pytest.raises(ValueError):
        a.latest_prompts = [
            "reply1",
            "reply2",
        ]  # latest_prompts size must match outputs size

    a = garak.attempt.Attempt()
    with pytest.raises(ValueError):
        a.outputs = ["oh no"]  # shouldn't be able to set outputs until prompt is there
