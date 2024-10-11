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
    assert isinstance(p.top_instructions, list) and len(p.top_instructions) > 0, "top_instructions must be a non-empty list"
    assert isinstance(p.contexts, list) and len(p.contexts) > 0, "contexts must be a non-empty list"
    assert isinstance(p.injection_sep_pairs, list) and len(p.injection_sep_pairs) > 0, "injection_sep_pairs must be a non-empty list"
    assert isinstance(p.injection_instructions, list) and len(p.injection_instructions) > 0, "injection_instructions must be a non-empty list"
    assert isinstance(p.payloads, list) and len(p.payloads) > 0, "payloads must be a non-empty list"
    assert isinstance(p.payload_triggers, list) and len(p.payload_triggers) > 0, "payload_triggers must be a non-empty list"

    for i in range(len(p.prompts)):
        assert (
            p.triggers[i] in p.prompts[i]
        ), "Each prompt must contain its accompanying trigger verbatim"
    assert isinstance(p.top_instructions, list)
    for _ti_e in enumerate(p.top_instructions):
        assert isinstance(
            _ti_e[1], str
        ), "Top-level instructions must be a string. index " + str(_ti_e[0])
    for _context_e in enumerate(p.contexts):
        assert garak.probes.latentinjection.INJECTION_MARKER in _context_e[1], (
            "Each context must contain an injection marker - missing f-string? index "
            + str(_context_e[0])
        )
    for _ii_e in enumerate(p.injection_instructions):
        assert garak.probes.latentinjection.PAYLOAD_MARKER in _ii_e[1], (
            "Each injection instruction must contain a payload marker - missing f-string? index "
            + str(_ii_e[0])
        )
    for _payload_e in enumerate(p.payloads):
        assert garak.probes.latentinjection.TRIGGER_MARKER in _payload_e[1], (
            "Each payload instruction must contain a trigger marker - missing f-string? index"
            + str(_payload_e[0])
        )
    for pair in p.injection_sep_pairs:
        assert len(pair) == 2, "separation pairs should have a start and end"
        assert isinstance(pair[0], str)
        assert isinstance(pair[1], str)
