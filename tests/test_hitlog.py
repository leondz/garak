# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import garak
import garak.cli


def test_hitlog_codepath():

    args = "-m test.Blank -p test.Test -d always.Fail".split()
    garak.cli.main(args)
