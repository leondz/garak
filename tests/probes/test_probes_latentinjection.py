# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _plugins
import garak.probes.base
import garak.probes.latentinjection

LATENT_INJECTION_PROBES = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("probes")
    if classname.startswith("probes.latentinjection")
]


@pytest.mark.parametrize("classname", LATENT_INJECTION_PROBES)
def test_latentinjection_structure(classname):
    p = _plugins.load_plugin(classname)
    assert isinstance(
        p, garak.probes.base.Probe
    ), "Latent injection probes must be instances of probes.base.Probe"
    assert len(p.prompts) == len(p.triggers), "Each prompt must have a matching trigger"
    for i in range(len(p.prompts)):
        assert (
            p.triggers[i] in p.prompts[i]
        ), "Each prompt must contain its accompanying trigger"
    assert isinstance(p.top_instructions, list)
    for _ti in p.top_instructions:
        assert isinstance(_ti, str), "Top-level instructions must be a string"
    for _context in p.contexts:
        assert (
            garak.probes.latentinjection.INJECTION_MARKER in _context
        ), "Each doc must contain an injection marker - missing f-string?"
    for _ii in p.injection_instructions:
        assert (
            garak.probes.latentinjection.PAYLOAD_MARKER in _ii
        ), "Each injection instruction must contain a payload marker - missing f-string?"
    for _payload in p.payloads:
        assert (
            garak.probes.latentinjection.TRIGGER_MARKER in _payload
        ), "Each payload instruction must contain a trigger marker - missing f-string?"
    for pair in p.injection_sep_pairs:
        assert len(pair) == 2, "separation pairs should have a start and end"
        assert isinstance(pair[0], str)
        assert isinstance(pair[1], str)
