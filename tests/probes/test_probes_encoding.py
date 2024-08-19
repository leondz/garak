# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

import garak.probes.encoding


@pytest.fixture
def p_config():
    return {"probes": {"encoding": {"generations": 5}}}


def test_InjectBase64_len_cap(p_config):
    p = garak.probes.encoding.InjectBase64(config_root=p_config)
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) < num_payloads * num_templates * num_encoders


def test_InjectBase64_prompt_trigger_match(p_config):
    p = garak.probes.encoding.InjectBase64(config_root=p_config)
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) == len(p.triggers)


def test_InjectBase64_triggers_not_in_prompts(p_config):
    p = garak.probes.encoding.InjectBase64(config_root=p_config)
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    for i in range(len(p.triggers)):
        assert p.triggers[i] not in p.prompts[i]


def test_encoding_payload_library_size_count(p_config):
    garak.probes.encoding._load_payloads()
    payload_count = len(garak.probes.encoding.payloads)
    p = garak.probes.encoding.InjectBase2048(config_root=p_config)
    assert len(garak.probes.encoding.payloads) == payload_count
    p = garak.probes.encoding.InjectZalgo(config_root=p_config)
    assert len(garak.probes.encoding.payloads) == payload_count
    p = garak.probes.encoding.InjectBase64(config_root=p_config)
    assert len(garak.probes.encoding.payloads) == payload_count
    garak.probes.encoding._load_payloads()
    assert len(garak.probes.encoding.payloads) == payload_count
