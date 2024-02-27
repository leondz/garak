#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# two tests:
# set buffs_include_original_prompt true
#  run test/lmrc.anthro
#  check that attempts w status 1 are original prompts + their lowercase versions
# set buffs_include_original_prompt false
#  run test/lmrc.anthro
#  check that attempts w status 1 are unique and have no uppercase characters

import json
import os
import pytest
import tempfile

import garak
import garak.cli


def test_include_original_prompt():
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(
            """---
plugins:
    buffs_include_original_prompt: true
reporting:
    report_prefix: buff_single
""".encode(
                "utf-8"
            )
        )
        garak.cli.main(
            f"-m test -p lmrc.Anthropomorphisation -b lowercase.Lowercase --config {tmp.name}".split()
        )

    prompts = []
    with open("buff_single.report.jsonl", "r", encoding="utf-8") as reportfile:
        for line in reportfile:
            r = json.loads(line)
            if r["entry_type"] == "attempt" and r["status"] == 1:
                prompts.append(r["prompt"])
    nonupper_prompts = set([])
    other_prompts = set([])
    for prompt in prompts:
        if prompt == prompt.lower() and prompt not in nonupper_prompts:
            nonupper_prompts.add(prompt)
        else:
            other_prompts.add(prompt)
    assert len(nonupper_prompts) >= len(other_prompts)
    assert len(nonupper_prompts) + len(other_prompts) == len(prompts)
    assert set(map(str.lower, prompts)) == nonupper_prompts


def test_exclude_original_prompt():
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(
            """---
plugins:
    buffs_include_original_prompt: false
reporting:
    report_prefix: buff_single
""".encode(
                "utf-8"
            )
        )
        garak.cli.main(
            f"-m test -p lmrc.Anthropomorphisation -b lowercase.Lowercase --config {tmp.name}".split()
        )

    prompts = []
    with open("buff_single.report.jsonl", "r", encoding="utf-8") as reportfile:
        for line in reportfile:
            r = json.loads(line)
            if r["entry_type"] == "attempt" and r["status"] == 1:
                prompts.append(r["prompt"])
    for prompt in prompts:
        assert prompt == prompt.lower()


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""

    def remove_buff_reports():
        os.remove("buff_single.report.jsonl")
        try:
            os.remove("buff_single.report.html")
            os.remove("buff_single.hitlog.jsonl")
        except FileNotFoundError:
            pass

    request.addfinalizer(remove_buff_reports)
