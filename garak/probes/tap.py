#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tree of Attacks with Pruning (TAP) probes.

LLM-generated prompts to jailbreak a target
"""
from pathlib import Path

from garak.probes.base import Probe


class TAPProbe(Probe):
    """Tree of Attacks with Pruning Probe"""

    bcp47 = "en"
    recommended_detector = ["mitigation.MitigationBypass"]
    tags = [
        "avid-effect:security:S0403",
        "avid-effect:performance:P0204",
        "quality:Security:PromptStability",
    ]
    goal = "cause the model to disregard the system prompt"
    uri = "https://arxiv.org/abs/2312.02119"

    def __init__(
            self,
            prompts_location: str = f"{Path(__file__).parents[1]}/resources/tap/data/tap_jailbreaks.txt"
    ):
        self.prompts_location = prompts_location

        with open(self.prompts_location, "r", encoding="utf-8") as f:
            prompts = f.readlines()
        if not prompts:
            msg = f"No prompts found in {self.prompts_location}"
            raise EOFError(msg)
        self.prompts = prompts
        super().__init__()
