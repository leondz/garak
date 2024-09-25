# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

import garak.attempt
import garak._plugins
import garak.detectors.base
import garak.detectors.misinfo

MISINFO_DETECTORS = [detector_name for (detector_name, active) in garak._plugins.enumerate_plugins("detectors") if detector_name.startswith("detectors.misinfo.")]

@pytest.mark.parametrize("misinfo_detector_name", MISINFO_DETECTORS)
def test_misinfo_detectors_init(misinfo_detector_name):
    d = garak._plugins.load_plugin(misinfo_detector_name)
    assert isinstance(d, garak.detectors.base.Detector), "each misinfo detector should be a Detector"

@pytest.mark.parametrize("anysent_detector_name", [anysent_name for anysent_name in MISINFO_DETECTORS if anysent_name.startswith("detectors.misinfo.AnySent")])
def test_misinfo_anysent(anysent_detector_name):
    d = garak._plugins.load_plugin(anysent_detector_name)
    trial_outputs = [
        "", 
        "Here's a phrase will no full stop", 
        f"Here's a phrase ending with the separator {garak.detectors.misinfo.ANYSENT_SENT_SEP}"
        f"Sentence 1{garak.detectors.misinfo.ANYSENT_SENT_SEP}Sentence 2"
    ]
    for trial_output in trial_outputs:
        a = garak.attempt.Attempt(prompt="The truth is just an excuse for lack of imagination.")
        a.outputs = [trial_output]
        result = d.detect(a)
        assert isinstance(result, list), f"{anysent_detector_name} should return a list"
        assert len(result) == 1, f"expected one result from {anysent_detector_name}"
        assert isinstance(result[0], float), f"{anysent_detector_name}'s list should return floats"

MULTISENT_OUTPUTS = [
    "This is good. No, this is bad.",
    "The claim is true. The claim is false.",
    "This is great. What terrible news"
]
@pytest.mark.parametrize("multisent_output", MULTISENT_OUTPUTS)
@pytest.mark.parametrize("anysent_detector_name", [anysent_name for anysent_name in MISINFO_DETECTORS if anysent_name.startswith("detectors.misinfo.AnySent")])
def test_misinfo_anysent_clip(anysent_detector_name, multisent_output):
    d = garak._plugins.load_plugin(anysent_detector_name)
    a = garak.attempt.Attempt(prompt="The truth is just an excuse for lack of imagination.")
    a.outputs = [multisent_output]
    a.notes["premise"] = "This is good"

    d.clip_last_sent = False
    unclipped_result = d.detect(a)
    d.clip_last_sent = True
    clipped_result = d.detect(a)
    assert unclipped_result != clipped_result, "clipping the last sentence should make a difference in these test cases"
