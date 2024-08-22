# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import pytest
import re

from garak import _plugins

DETECTORS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins(
        "detectors", skip_base_classes=False
    )
]

bcp_lenient_re = re.compile(r"[a-z]{2}([\-A-Za-z]*)")


@pytest.mark.parametrize("classname", DETECTORS)
def test_detector_metadata(classname):
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
            bcp_lenient_re, bcp47_part
        ), "langs must be described with either * or a bcp47 code"
    assert isinstance(
        d.doc_uri, str
    ), "detectors should give a doc uri describing/citing the attack"
    if len(d.doc_uri) > 1:
        assert d.doc_uri.lower().startswith(
            "http"
        ), "doc uris should be fully-specified absolute HTTP addresses"
