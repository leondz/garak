# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
import pytest

from garak import _plugins
from garak.exception import APIKeyMissingError
from garak.attempt import Attempt

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
    a.prompt = ""
    a.outputs = ["", None]
    try:
        results = di.detect(a)
    except APIKeyMissingError:
        pytest.skip("API key unavailable")

    assert isinstance(results, list), "detect() should return a list"
    for entry in results:
        assert isinstance(entry, float), "detect() must return a list of floats"
        assert 0.0 <= entry <= 1.0, "detect() values should be between 0.0 and 1.0"
        assert len(results) <= len(
            a.outputs
        ), "detect() should return no more values than # attempt outputs provided"
