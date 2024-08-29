# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import garak.probes.packagehallucination


def test_promptcount():
    p_python = garak.probes.packagehallucination.Python()
    p_ruby = garak.probes.packagehallucination.Ruby()
    p_javascript = garak.probes.packagehallucination.JavaScript()

    expected_count = len(garak.probes.packagehallucination.stub_prompts) * len(
        garak.probes.packagehallucination.code_tasks
    )

    assert (
        len(p_python.prompts) == expected_count
    ), f"Python prompt count mismatch. Expected {expected_count}, got {len(p_python.prompts)}"
    assert (
        len(p_ruby.prompts) == expected_count
    ), f"Ruby prompt count mismatch. Expected {expected_count}, got {len(p_ruby.prompts)}"
    assert (
        len(p_javascript.prompts) == expected_count
    ), f"JavaScript prompt count mismatch. Expected {expected_count}, got {len(p_javascript.prompts)}"
