# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import csv
import json
import tempfile

import pytest

import garak._config
import garak.exception
import garak.payloads


PAYLOAD_NAMES = list(
    garak.payloads.Loadmaster().search()
)  # default includes local custom payloads to help test them


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_core_payloads(payload_name):
    l = garak.payloads.Loadmaster()
    p = l.load(payload_name)
    assert isinstance(
        p, garak.payloads.PayloadGroup
    ), f"Not a valid payload: {payload_name}"


@pytest.fixture(scope="module")
def payload_typology():
    types = []
    with open(
        garak._config.transient.package_dir / "resources" / "typology_payloads.tsv",
        "r",
        encoding="utf-8",
    ) as typology_file:
        r = csv.reader(typology_file, delimiter="\t")
        for row in r:
            types.append(row[0])
    return types


def test_payload_Loadmaster():
    l = garak.payloads.Loadmaster()
    assert isinstance(l, garak.payloads.Loadmaster)


def test_payload_list():
    l = garak.payloads.Loadmaster()
    for payload_name in l.search():
        assert isinstance(
            payload_name, str
        ), "Payload names from Loadmaster().search() must be strings"


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_payloads_have_valid_tags(payload_name, payload_typology):
    l = garak.payloads.Loadmaster()
    p = l.load(payload_name)
    for typee in p.types:
        assert (
            typee in payload_typology
        ), f"Payload {payload_name} type {typee} not found in payload typology"


def test_nonexistent_payload_direct_load():
    with pytest.raises(FileNotFoundError):
        garak.payloads._load_payload("jkasfohgi")


def test_nonexistent_payload_manager_load():
    l = garak.payloads.Loadmaster()
    with pytest.raises(garak.exception.PayloadFailure):
        p = l.load("mydeardoctor")


def test_non_json_direct_load():
    with tempfile.NamedTemporaryFile() as t:
        with pytest.raises(
            garak.exception.PayloadFailure
        ):  # blank file aint valid json
            garak.payloads._load_payload("jkasfohgi", t.name)


OK_PAYLOADS = [
    {"garak_payload_name": "test", "payloads": ["pay", "load"], "payload_types": []},
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "payload_types": [],
        "bcp47": "en",
    },
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "payload_types": [],
        "detector_name": "detector",
    },
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "payload_types": [],
        "detector_name": "",
    },
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "payload_types": [],
        "detector_name": "llmaaj",
        "detector_config": {"model": "x"},
    },
]

BAD_PAYLOADS = [
    {"garak_payload_name": "test"},
    {"payloads": ["pay", "load"]},
    {"payload_strings": ["pay", "load"]},
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "payload_types": "Security circumvention instructions",
    },
    {"garak_payload_name": "test", "payloads": ["pay", "load"], "lang": "en"},
    {"garak_payload_name": "test", "payloads": ["pay", "load"], "detector_params": {}},
    {"garak_payload_name": "test", "payloads": ["pay", "load"], "detector_config": {}},
    {
        "garak_payload_name": "test",
        "payloads": ["pay", "load"],
        "detector_name": "",
        "detector_config": {"model": "x"},
    },
]


@pytest.mark.parametrize("payload", OK_PAYLOADS)
def test_payload_schema_validation_ok(payload):
    assert garak.payloads._validate_payload(payload) is True


@pytest.mark.parametrize("payload", BAD_PAYLOADS)
def test_payload_schema_validation_bad(payload):
    assert garak.payloads._validate_payload(payload) != True
