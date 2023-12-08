#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess

import pytest

from garak import cli

temp_prefix = "_garak_internal_test_temp"


@pytest.fixture(scope="session", autouse=True)
def garak_tiny_run() -> None:
    cli.main(["-m", "test.Blank", "-p", "test.Blank", "--report_prefix", temp_prefix])


def test_analyze_log_runs():
    result = subprocess.run(
        ["python3", "analyze/analyze_log.py", temp_prefix + ".report.jsonl"],
        check=True,
    )
    assert result.returncode == 0


def test_report_digest_runs():
    result = subprocess.run(
        ["python3", "analyze/report_digest.py", temp_prefix + ".report.jsonl"],
        check=True,
    )
    assert result.returncode == 0


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""

    def remove_logs():
        os.remove(temp_prefix + ".report.jsonl")

    request.addfinalizer(remove_logs)
