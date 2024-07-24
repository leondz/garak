# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import contextlib
import os
import pytest

import garak
import garak.cli


CODEPATH_PREFIX = "_garak_test_hitlog_codepath"


def test_hitlog_codepath():

    args = f"-m test.Blank --report_prefix {CODEPATH_PREFIX} -p test.Test -d always.Fail".split()
    garak.cli.main(args)
    assert os.path.isfile(f"{CODEPATH_PREFIX}.hitlog.jsonl")
