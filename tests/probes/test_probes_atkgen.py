# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import tempfile
import importlib

import garak._config
import garak._plugins
import garak.attempt
import garak.generators
import garak.probes.atkgen
import garak.probes.base
import pytest
from garak import _config, _plugins
from garak._config import transient
from garak.probes.atkgen import TEMPLATE_PLACEHOLDER
import garak
import importlib


def test_atkgen_tox_load():
    importlib.reload(
        garak._config
    )  # this might indicate more test need `_config` reset
    p = garak._plugins.load_plugin("probes.atkgen.Tox")
    assert isinstance(p, garak.probes.base.Probe)
    for k, v in p.DEFAULT_PARAMS.items():
        if k == "red_team_model_config":
            continue
        assert getattr(p, k) == v


def test_atkgen_config():
    p = garak._plugins.load_plugin("probes.atkgen.Tox")
    rt_mod, rt_klass = p.red_team_model_type.split(".")
    assert p.red_team_model_config == {
        "generators": {
            rt_mod: {
                rt_klass: {
                    "hf_args": {"device": "cpu", "torch_dtype": "float32"},
                    "name": p.red_team_model_name,
                }
            }
        }
    }


def test_atkgen_one_pass():
    garak._config.load_base_config()
    garak._config.plugins.probes["atkgen"][
        "generations"
    ] = 1  # we only need one conversation
    p = garak._plugins.load_plugin("probes.atkgen.Tox", config_root=garak._config)
    p.max_calls = 1  # we don't need a full conversation
    g = garak._plugins.load_plugin("generators.test.Repeat", config_root=garak._config)
    with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
        garak._config.transient.reportfile = temp_report_file
        garak._config.transient.report_filename = temp_report_file.name
        result = p.probe(g)
    assert isinstance(
        p.redteamer, garak.generators.base.Generator
    ), "atkgen redteamer should be a generator"
    assert isinstance(result, list), "probe results should be a list"
    assert isinstance(
        result[0], garak.attempt.Attempt
    ), "probe results should be a list of attempt.Attempt"
    assert "turns" in result[0].notes, "atkgen attempts should have a list of turns"
    assert isinstance(
        result[0].notes["turns"], list
    ), "atkgen attempts should have a list of turns"
    assert (
        result[0].notes["turns"][0][0] == "probe"
    ), "probe takes the first turn in atkgen"
    assert (
        len(result[0].notes["turns"][0][1]) > 0
    ), "atkgen probe first turn should not be blank"


def test_atkgen_custom_model():
    red_team_model_type = "test.Single"
    red_team_model_name = ""
    garak._config.load_base_config()
    rt_custom_generator_config = {
        "probes": {
            "atkgen": {
                "Tox": {
                    "red_team_model_type": red_team_model_type,
                    "red_team_model_name": red_team_model_name,
                    "generations": 1,  # we only need one conversation
                }
            }
        }
    }
    p = garak._plugins.load_plugin(
        "probes.atkgen.Tox", config_root=rt_custom_generator_config
    )
    p.max_calls = 1  # we don't need a full conversation
    assert (
        p.red_team_model_type == red_team_model_type
    ), "red team model type config should be loaded"
    assert (
        p.red_team_model_name == red_team_model_name
    ), "red team model name config should be loaded"
    g = garak._plugins.load_plugin("generators.test.Repeat", config_root=garak._config)
    with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
        garak._config.transient.reportfile = temp_report_file
        garak._config.transient.report_filename = temp_report_file.name
        result = p.probe(g)
    assert (
        p.redteamer.name == red_team_model_type.split(".")[-1]
    ), "loaded red team model name should match configured name"
    assert p.redteamer.fullname == red_team_model_type.replace(".", ":").title()


@pytest.mark.parametrize("classname", [
    "probes.atkgen.Tox"
])
def test_atkgen_initialization(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    atkgen_class = getattr(mod, class_name)
    atkgen_instance = atkgen_class(config_root=_config)
    assert isinstance(atkgen_instance, atkgen_class), f"{classname} initialization failed"


@pytest.mark.parametrize("classname", [
    "probes.atkgen.Tox" 
])
def test_atkgen_translation(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    atkgen_class = getattr(mod, class_name)
    _config.run.translation_service = 'local'
    _config.run.lang_spec = 'jap'
    _config.run.seed = 42
    atkgen_instance = atkgen_class(config_root=_config)
    if hasattr(atkgen_instance, '_translate'):
        translated_prompts = atkgen_instance._translate([TEMPLATE_PLACEHOLDER])
        assert isinstance(translated_prompts, list)
        assert len(translated_prompts) > 0
        assert translated_prompts[1] != TEMPLATE_PLACEHOLDER


@pytest.mark.parametrize("classname", [
    "probes.atkgen.Tox" 
])
def test_atkgen_probe(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    atkgen_class = getattr(mod, class_name)
    _config.system.verbose = 1
    _config.system.parallel_requests = 1
    with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
        _config.transient.reportfile = temp_report_file
        _config.transient.report_filename = temp_report_file.name
        _config.plugins.generators = {}
        atkgen_instance = atkgen_class(config_root=_config)
        generator = _plugins.load_plugin("generators.test.Repeat", config_root=_config)  # Replace with an actual generator instance if available
        attempts = atkgen_instance.probe(generator)
        assert isinstance(attempts, list), "probe method should return a list of attempts"
        assert len(attempts) > 0, "probe method should return at least one attempt"
        assert isinstance(attempts[0], garak.attempt.Attempt), "probe results should be a list of attempt.Attempt"
        assert "turns" in attempts[0].notes, "atkgen attempts should have a list of turns"
        assert isinstance(attempts[0].notes["turns"], list), "atkgen attempts should have a list of turns"
        assert attempts[0].notes["turns"][0][0] == "probe", "probe takes the first turn in atkgen"
        assert len(attempts[0].notes["turns"][0][1]) > 0, "atkgen probe first turn should not be blank"
    importlib.reload(garak._config)
    garak._config.load_base_config()
