# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
import pytest
import types

from garak import _plugins
from garak.attempt import Attempt
from garak.exception import APIKeyMissingError
import garak.detectors.base

DEFAULT_GENERATOR_NAME = "garak test"
DEFAULT_PROMPT_TEXT = "especially the lies"


DETECTORS = [
    classname for (classname, active) in _plugins.enumerate_plugins("detectors")
]


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

    a = Attempt()
    # dressing required to get 'some' detectors to return results
    a.notes["trigger"] = "x"
    a.notes["triggers"] = ["x", "x", "x", "x"]
    a.notes["repeat_word"] = "x"

    a.prompt = ""
    a.notes["format"] = "local filename"
    a.outputs = ["", None]
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
    assert list(d.detect(a)) == []
