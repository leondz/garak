#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Topic probe

Attempt to get a model to engage on a number of contentious topics
"""


from garak.probes.base import Probe


class PushConversation(Probe):
    """See if a model starts giving other data when asked to repeat a string indefinitely"""

    bcp47 = "*"
    primary_detector = "replay.RepeatDiverges"
    extended_detectors = ["mitigation.MitigationBypass"]
    goal = "get the model to leak data by asking it to repeat words"
    uri = "https://not-just-memorization.github.io/extracting-training-data-from-chatgpt.html"
    tags = [
        "avid-effect:security:S0301",
        "owasp:llm10",
        "owasp:llm06",
        "quality:Security:Confidentiailty",
    ]  # MISP-format taxonomy categories
