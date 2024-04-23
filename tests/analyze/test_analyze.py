# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys

import pytest

from garak import cli

temp_prefix = "_garak_internal_test_temp"


@pytest.fixture(scope="session", autouse=True)
def garak_tiny_run() -> None:
    cli.main(["-m", "test.Blank", "-p", "test.Blank", "--report_prefix", temp_prefix])


def test_analyze_log_runs():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "garak.analyze.analyze_log",
            temp_prefix + ".report.jsonl",
        ],
        check=True,
    )
    assert result.returncode == 0


def test_report_digest_runs():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "garak.analyze.report_digest",
            temp_prefix + ".report.jsonl",
        ],
        check=True,
    )
    assert result.returncode == 0


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""

    def remove_logs():
        logs = [
            temp_prefix + ".report.jsonl",
            temp_prefix + ".report.html",
        ]
        for file in logs:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass

    request.addfinalizer(remove_logs)
