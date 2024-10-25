# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
import pytest
import re
import types

import garak
from garak import _plugins
from garak.attempt import Attempt
from garak.configurable import Configurable
from garak.detectors.misleading import MustRefuteClaimModel, MustRefuteClaimKW, MustContradictNLI
from garak.exception import APIKeyMissingError
import garak.detectors.base
import pytest
from garak.attempt import Attempt
from garak import _config
import importlib


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_translate_substrings(claim_detector):
    translated_substrings = claim_detector.substrings
    assert isinstance(translated_substrings, list), "Translation should return a list"
    assert len(translated_substrings) > 0, "Translation should produce non-empty results"
    half_length = len(translated_substrings) // 2
    for i in range(half_length):
        assert translated_substrings[i] != translated_substrings[half_length + i], "Each word should be translated"


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_hf_detector_detection(hf_detector):
    # Create a sample Attempt with Japanese text
    attempt = Attempt(prompt="2人の女性が持ち帰り用の荷物を持ちながら抱き合っている")
    attempt.outputs = ["男たちがデリカテッセンの外で喧嘩している"]

    # Run the detection
    results = hf_detector.detect(attempt)
    # Verify the results
    assert isinstance(results, list), "Detect method should return a list"
    for result in results:
        assert isinstance(result, float), "Each result should be a float"
        assert 0.0 <= result <= 1.0, "Each result should be between 0.0 and 1.0"