# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from garak import _plugins
from garak import _config
import garak.generators.base
import garak.generators.nvcf

# please refactor me before adding a single more test 😭

def test_instantiate():
    _config.plugins.generators["nvcf"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"]["name"] = "placeholder name"
    _config.plugins.generators["nvcf"]["NvcfChat"]["api_key"] = "placeholder key"
    g = _plugins.load_plugin("generators.nvcf.NvcfChat")
    assert isinstance(g, garak.generators.base.Generator)

    _config.plugins.generators["nvcf"]["NvcfCompletion"] = {}
    _config.plugins.generators["nvcf"]["NvcfCompletion"]["name"] = "placeholder name"
    _config.plugins.generators["nvcf"]["NvcfCompletion"]["api_key"] = "placeholder key"
    g = _plugins.load_plugin("generators.nvcf.NvcfCompletion")
    assert isinstance(g, garak.generators.base.Generator)


def test_version_endpoint():
    name = "feedfacedeadbeef"
    version = "cafebabe"
    _config.plugins.generators["nvcf"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"]["name"] = name
    _config.plugins.generators["nvcf"]["NvcfChat"]["api_key"] = "placeholder key"
    _config.plugins.generators["nvcf"]["NvcfChat"]["version_id"] = version
    g = _plugins.load_plugin("generators.nvcf.NvcfChat")
    assert g.invoke_url == f"{g.invoke_url_base}{name}/versions/{version}"


def test_custom_keys():
    name = "feedfacedeadbeef"
    params = {"n": 1, "model": "secret/model_1.8t"}
    _config.plugins.generators["nvcf"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"] = {}
    _config.plugins.generators["nvcf"]["NvcfChat"]["name"] = name
    _config.plugins.generators["nvcf"]["NvcfChat"]["api_key"] = "placeholder key"
    _config.plugins.generators["nvcf"]["NvcfChat"]["extra_params"] = params
    g = _plugins.load_plugin("generators.nvcf.NvcfChat")
    test_payload = g._build_payload("whatever prompt")
    for k, v in params.items():
        assert test_payload[k] == v
