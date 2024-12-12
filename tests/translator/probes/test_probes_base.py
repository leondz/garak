# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import pytest
import re

from garak import _config, _plugins
import garak
import tempfile
from garak.harnesses.base import Harness
from garak.translator import is_english
import os
import torch


NON_PROMPT_PROBES = ["probes.dan.AutoDAN", "probes.tap.TAP"]
ATKGEN_PROMPT_PROBES = ["probes.atkgen.Tox", "probes.dan.Dan_10_0"] 
VISUAL_PROBES = ["probes.visual_jailbreak.FigStep", "probes.visual_jailbreak.FigStepTiny"]
PROBES = [classname for (classname, active) in _plugins.enumerate_plugins("probes") 
    if classname not in NON_PROMPT_PROBES and classname not in VISUAL_PROBES and classname not in ATKGEN_PROMPT_PROBES]
openai_api_key_missing = not os.getenv("OPENAI_API_KEY")


def load_module_for_test(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    _config.run.seed = 42
    probe_instance = probe_class(config_root=_config)
    local_config_path =str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation_local_low.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    return probe_instance


def make_prompt_list(result):
    prompt_list = []
    for attempt in result:
        for messages in attempt.messages:
            for message in messages:
                prompt_list.append(message["content"])
    return prompt_list


"""
Skip probes.tap.PAIR because it needs openai api key and large gpu resource
"""
@pytest.mark.parametrize("classname", ATKGEN_PROMPT_PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_atkgen_probe_translation(classname):
    probe_instance = load_module_for_test(classname)
    if probe_instance.bcp47 != "en" or classname == "probes.tap.PAIR":
        importlib.reload(garak._config)
        garak._config.load_base_config()
        return

    g = garak._plugins.load_plugin("generators.test.Repeat", config_root=garak._config)
    translator_instance = probe_instance.get_translator()
    with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
        garak._config.transient.reportfile = temp_report_file
        garak._config.transient.report_filename = temp_report_file.name
        probe_instance.translator = translator_instance
        result = probe_instance.probe(g)
        prompt_list = make_prompt_list(result)
        assert prompt_list[0] == prompt_list[1]
        assert prompt_list[0] != prompt_list[2]
        assert prompt_list[0] != prompt_list[3]

    importlib.reload(garak._config)
    garak._config.load_base_config()


@pytest.mark.parametrize("classname", PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_probe_prompt_translation(classname):
    probe_instance = load_module_for_test(classname)
    if probe_instance.bcp47 != "en" or classname == "probes.tap.PAIR":
        importlib.reload(garak._config)
        garak._config.load_base_config()
        return
    
    translator_instance = probe_instance.get_translator()
    if hasattr(probe_instance, 'triggers'):
        original_triggers = probe_instance.triggers[:2]
        translate_triggers = translator_instance.translate_triggers(original_triggers)
        assert len(translate_triggers) >= len(original_triggers)

    original_prompts = probe_instance.prompts[:2]
    probe_instance.prompts = original_prompts
    g = garak._plugins.load_plugin("generators.test.Repeat", config_root=garak._config)
    with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
        garak._config.transient.reportfile = temp_report_file
        garak._config.transient.report_filename = temp_report_file.name
        probe_instance.generations = 1
        result = probe_instance.probe(g)
        org_message_list = make_prompt_list(result)

        probe_instance.translator = translator_instance
        result = probe_instance.probe(g)
        message_list = make_prompt_list(result)
        assert len(org_message_list) <= len(message_list)

    importlib.reload(garak._config)
    garak._config.load_base_config()
