# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import garak.probes.encoding
from garak import _config, _plugins
from garak.translator import is_english
import pytest
import garak
import importlib

PROBES = [classname for (classname, active) 
    in _plugins.enumerate_plugins("probes") if "encoding" in classname]

def test_InjectBase64_len_cap():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) < num_payloads * num_templates * num_encoders


@pytest.fixture(scope="function")
def test_InjectBase64_prompt_trigger_match():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) == len(p.triggers)


@pytest.fixture(scope="function")
def test_InjectBase64_triggers_not_in_prompts():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    for i in range(len(p.triggers)):
        assert p.triggers[i] not in p.prompts[i]


def test_encoding_payload_library_size_count():
    garak.probes.encoding._load_payloads()
    payload_count = len(garak.probes.encoding.payloads)
    p = garak.probes.encoding.InjectBase2048()
    assert len(garak.probes.encoding.payloads) == payload_count
    p = garak.probes.encoding.InjectZalgo()
    assert len(garak.probes.encoding.payloads) == payload_count
    p = garak.probes.encoding.InjectBase64()
    assert len(garak.probes.encoding.payloads) == payload_count
    garak.probes.encoding._load_payloads()
    assert len(garak.probes.encoding.payloads) == payload_count
