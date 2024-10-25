# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import pytest
import re

from garak import _config, _plugins
import garak
import tempfile

PROBES = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]

DETECTORS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins(
        "detectors", skip_base_classes=False
    )
]
DETECTOR_BARE_NAMES = [".".join(d.split(".")[1:]) for d in DETECTORS]

BCP_LENIENT_RE = re.compile(r"[a-z]{2}([\-A-Za-z]*)")

with open(
    _config.transient.package_dir / "data" / "misp_descriptions.tsv",
    "r",
    encoding="utf-8",
) as misp_data:
    MISP_TAGS = [line.split("\t")[0] for line in misp_data.read().split("\n")]


@pytest.mark.parametrize("classname", PROBES)
def test_detector_specified(classname):  # every probe should give detector(s)
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    assert (
        isinstance(probe_class.primary_detector, str)
        or len(probe_class.recommended_detector) > 0
    )


@pytest.mark.parametrize("classname", PROBES)
def test_probe_detector_exists(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    probe_detectors = probe_class.recommended_detector + probe_class.extended_detectors
    if probe_class.primary_detector is not None:
        probe_detectors += [probe_class.primary_detector]
    assert set(probe_detectors).issubset(DETECTOR_BARE_NAMES)


@pytest.mark.parametrize("classname", PROBES)
def test_probe_structure(classname):

    m = importlib.import_module("garak." + ".".join(classname.split(".")[:-1]))
    c = getattr(m, classname.split(".")[-1])

    # any parameter that has a default must be supported
    unsupported_defaults = []
    if c._supported_params is not None:
        if hasattr(g, "DEFAULT_PARAMS"):
            for k, _ in c.DEFAULT_PARAMS.items():
                if k not in c._supported_params:
                    unsupported_defaults.append(k)
    assert unsupported_defaults == []


@pytest.mark.parametrize("classname", PROBES)
def test_probe_metadata(classname):
    p = _plugins.load_plugin(classname)
    assert isinstance(p.goal, str), "probe goals should be a text string"
    assert len(p.goal) > 0, "probes must state their general goal"
    assert isinstance(
        p.bcp47, str
    ), "language codes should be described in a comma-separated string of bcp47 tags or *"
    bcp47_parts = p.bcp47.split(",")
    for bcp47_part in bcp47_parts:
        assert bcp47_part == "*" or re.match(
            BCP_LENIENT_RE, bcp47_part
        ), "langs must be described with either * or a bcp47 code"
    assert isinstance(
        p.doc_uri, str
    ), "probes should give a doc uri describing/citing the attack"
    if len(p.doc_uri) > 1:
        assert p.doc_uri.lower().startswith(
            "http"
        ), "doc uris should be fully-specified absolute HTTP addresses"
    assert isinstance(p.modality, dict), "probes need to describe available modalities"
    assert "in" in p.modality, "probe modalities need an in descriptor"
    assert isinstance(p.modality["in"], set), "modality descriptors must be sets"


@pytest.mark.parametrize("plugin_name", PROBES)
def test_check_docstring(plugin_name):
    plugin_name_parts = plugin_name.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    doc = getattr(getattr(mod, class_name), "__doc__")
    doc_paras = re.split(r"\s*\n\s*\n\s*", doc)
    assert (
        len(doc_paras) >= 2
    )  # probe class doc should have a summary, two newlines, then a paragraph giving more depth, then optionally more words
    assert (
        len(doc_paras[0]) > 0
    )  # the first paragraph of the probe docstring should not be empty


@pytest.mark.parametrize("classname", PROBES)
def test_tag_format(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name)
    assert (
        cls.tags != [] or cls.active == False
    )  # all probes should have at least one tag
    for tag in cls.tags:  # should be MISP format
        assert type(tag) == str
        for part in tag.split(":"):
            assert re.match(r"^[A-Za-z0-9_\-]+$", part)
        if tag.split(":")[0] != "payload":
            assert tag in MISP_TAGS


"""
Skip probes.tap.PAIR because it needs openai api key and large gpu resource
"""
@pytest.mark.parametrize("classname", PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_probe_translation(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe_instance = probe_class(config_root=_config)
    if probe_instance.bcp47 != "en" or classname == "probes.tap.PAIR":
        importlib.reload(garak._config)
        garak._config.load_base_config()
        return
    if hasattr(probe_instance, 'prompts') is False or len(probe_instance.prompts) == 0:
        with tempfile.NamedTemporaryFile(mode="w+") as temp_report_file:
            _config.transient.reportfile = temp_report_file
            _config.transient.report_filename = temp_report_file.name
            _config.system.verbose = 1
            _config.system.parallel_requests = 1
            _config.system.parallel_attempts = 2
            generator = _plugins.load_plugin("generators.test.Repeat", config_root=_config)  # Replace with an actual generator instance if available
            attempts = probe_instance.probe(generator)
            if len(attempts) > 1:
                prompt_list = [value for dict_list in attempts[0].messages[0] for key, value in dict_list.items() if key == "content"] 
                for i in range(len(prompt_list) - 3, 3):
                    assert prompt_list[i] == prompt_list[i + 1]
                    assert prompt_list[i] != prompt_list[i + 2]
                    assert prompt_list[i] != prompt_list[i + 3]
            else:
                prompt_list = ["hello", "test"]
                translated_prompts = probe_instance.translator.translate_prompts(prompt_list)
                for index, prompt in enumerate(prompt_list):
                    if probe_instance.translator.judge_list[index] is True:
                        assert translated_prompts[len(prompt_list) + index] != prompt
                    else:
                        assert translated_prompts[len(prompt_list) + index] == prompt
    else:
        probe_instance.translator.target_lang = 'jap'
        probe_instance.translator.lang_specs = 'jap'
        probe_instance.translator._load_model()
        if hasattr(probe_instance, 'translator'):
            assert hasattr(probe_instance, 'translator'), f"{classname} does not have a translator attribute"
            if type(probe_instance.prompts[0]) is dict:
                prompt_list = [value for dict_list in probe_instance.prompts for key, value in dict_list.items() if key == "text"] 
                translated_prompts = probe_instance.translator.translate_prompts(prompt_list)
            else:
                translated_prompts = probe_instance.translator.translate_prompts(probe_instance.prompts)
            assert isinstance(translated_prompts, list)
            assert len(translated_prompts) > 0
            for index, prompt in enumerate(probe_instance.prompts):
                if probe_instance.translator.judge_list[index] is True:
                    assert translated_prompts[len(probe_instance.prompts) + index] != probe_instance.prompts[index]
                else:
                    assert translated_prompts[len(probe_instance.prompts) + index] == probe_instance.prompts[index]
    importlib.reload(garak._config)
    garak._config.load_base_config()
