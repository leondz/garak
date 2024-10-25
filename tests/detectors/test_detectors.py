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
from garak.detectors.base import Detector
from garak.exception import APIKeyMissingError
import garak.detectors.base
import pytest
from garak.attempt import Attempt
from garak import _config
import importlib


DEFAULT_GENERATOR_NAME = "garak test"
DEFAULT_PROMPT_TEXT = "especially the lies"


DETECTORS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("detectors")
    if classname
    not in [  # filter detector classes used as templates
        "detectors.packagehallucination.PackageHallucinationDetector",
    ]
]

BCP_LENIENT_RE = re.compile(r"[a-z]{2}([\-A-Za-z]*)")


@pytest.mark.parametrize("classname", DETECTORS)
def test_detector_structure(classname):

    m = importlib.import_module("garak." + ".".join(classname.split(".")[:-1]))
    d = getattr(m, classname.split(".")[-1])

    # has method detect
    assert "detect" in dir(d), f"detector {classname} must have a method detect"
    # _call_model has a generations_this_call param
    assert (
        "attempt" in inspect.signature(d.detect).parameters
    ), f"{classname}.detect() must accept parameter attempt"
    # any parameter that has a default must be supported
    unsupported_defaults = []
    if d._supported_params is not None:
        if hasattr(d, "DEFAULT_PARAMS"):
            for k, _ in d.DEFAULT_PARAMS.items():
                if k not in d._supported_params:
                    unsupported_defaults.append(k)
    assert unsupported_defaults == []


@pytest.mark.parametrize("classname", DETECTORS)
def test_detector_detect(classname):

    m = importlib.import_module("garak." + ".".join(classname.split(".")[:-1]))
    dc = getattr(m, classname.split(".")[-1])
    try:
        di = dc.__new__(dc)
        di.__init__()
    except APIKeyMissingError:
        pytest.skip("API key unavailable")

    assert isinstance(di, Detector), "detectors must eventually inherit from Detector"
    assert isinstance(di, Configurable), "detectors must be configurable"

    a = Attempt()
    # dressing required to get 'some' detectors to return results
    a.notes["trigger"] = "x"
    a.notes["triggers"] = ["x", "x", "x", "x"]
    a.notes["repeat_word"] = "x"

    a.prompt = ""
    a.notes["format"] = "local filename"
    a.outputs = ["", None]
    a.detector_results = {"x": [0.0]}
    try:
        results = di.detect(a)
    except APIKeyMissingError:
        pytest.skip("API key unavailable")

    assert isinstance(
        results, (list, types.GeneratorType)
    ), "detect() should return an ordered iterable"
    for entry in results:
        # detect() should skip non-evaluated items from output. NB this breaks output:result alignment
        assert isinstance(entry, float), "detect() must return a list of floats"
        assert 0.0 <= entry <= 1.0, "detect() values should be between 0.0 and 1.0"
        assert len(list(results)) <= len(
            list(a.outputs)
        ), "detect() should return no more values than # attempt outputs provided"

    if classname == "detectors.always.Passthru":
        return

    a.outputs = ["Terok", "Nor"]
    assert (
        len(a.all_outputs) == 4
    ), "we've supplied four outputs to the attempt, should have four logged"
    results = di.detect(a)
    if not isinstance(
        di, garak.detectors.base.FileDetector
    ):  # this returns nothing - remove when Nones are OK in detector output
        assert len(list(results)) in (
            3,
            4,
        ), "detector should return as many results as in all_outputs (maybe excluding Nones)"


def test_filedetector_nonexist():
    d = garak.detectors.base.FileDetector()
    a = garak.attempt.Attempt(prompt="")
    a.outputs = [None, "", "/non/existing/file"]
    a.notes["format"] = d.valid_format
    assert (
        len(list(d.detect(a))) == 0
    ), "FileDetector should skip filenames for non-existing files"


@pytest.mark.parametrize("classname", DETECTORS)
def test_detector_metadata(classname):
    if classname.startswith("detectors.base."):
        return
    # instantiation can fail e.g. due to missing API keys
    # luckily this info is descriptive rather than behaviour-altering, so we don't need an instance
    m = importlib.import_module("garak." + ".".join(classname.split(".")[:-1]))
    dc = getattr(m, classname.split(".")[-1])
    d = dc.__new__(dc)
    assert isinstance(
        d.bcp47, str
    ), "language codes should be described in a comma-separated string of bcp47 tags or *"
    bcp47_parts = d.bcp47.split(",")
    for bcp47_part in bcp47_parts:
        assert bcp47_part == "*" or re.match(
            BCP_LENIENT_RE, bcp47_part
        ), "langs must be described with either * or a bcp47 code"
    assert isinstance(d.doc_uri, str) or d.doc_uri is None
    if isinstance(d.doc_uri, str):
        assert len(d.doc_uri) > 1, "string doc_uris must be populated. else use None"
        assert d.doc_uri.lower().startswith(
            "http"
        ), "doc uris should be fully-specified absolute HTTP addresses"


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_translate_keywords(detector):
    substrings = ["test", "example"]
    translated = detector.translator.translate_prompts(substrings)
    assert isinstance(translated, list), "Translation should return a list"
    assert len(translated) > 0, "Translation should produce non-empty results"
    for index, keyword in enumerate(substrings):
        assert keyword != translated[len(substrings) + index], "Each word should be translated"


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_translate_substrings(detector_string):
    translated_substrings = detector_string.substrings
    assert isinstance(translated_substrings, list), "Translation should return a list"
    assert len(translated_substrings) > 0, "Translation should produce non-empty results"
    half_length = len(translated_substrings) // 2
    for i in range(half_length):
        assert translated_substrings[i] != translated_substrings[half_length + i], "Each word should be translated"
    attempt = Attempt(prompt="This is a test prompt")
    attempt.outputs = [
        '1', 
        '2 example', 
        '3 試錬 を', 
        '4 それ は 作り話 と な る ため な の で あ る.'
    ]
    results = detector_string.detect(attempt)
    assert results == [0.0, 1.0, 0.0, 1.0]

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