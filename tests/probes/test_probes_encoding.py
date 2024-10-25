# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import garak.probes.encoding
from garak.probes.encoding import BaseEncodingProbe, InjectBase16, InjectBase32, InjectAscii85, \
                                        InjectHex, InjectQP, InjectUU, InjectMime, \
                                        InjectROT13, InjectBase2048, InjectBraille, \
                                        InjectMorse, InjectNato, InjectEcoji, InjectZalgo
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


@pytest.mark.parametrize("classname", PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_inject_translation(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    inject_class = getattr(mod, class_name)

    class TestProbe(inject_class):
        encoding_funcs = [lambda x: x]
        encoding_name = "TEST"

        def __init__(self, config_root=_config):
            super().__init__(config_root=config_root)

    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe_instance = TestProbe(config_root=_config)
    translated_triggers = probe_instance.translator.translate_prompts(probe_instance.triggers)
    assert isinstance(translated_triggers, list), "_translate should return a list"
    assert len(translated_triggers) > len(probe_instance.triggers), "_translate should add translated triggers"
    for index, prompt in enumerate(probe_instance.triggers):
        each_translated_trigger = translated_triggers[len(probe_instance.triggers) + index]
        if is_english(prompt) and is_english(each_translated_trigger) is False:
            assert each_translated_trigger != prompt
    importlib.reload(garak._config)
    garak._config.load_base_config()
