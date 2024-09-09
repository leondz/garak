# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import csv

import pytest

import garak._config
import garak.payloads


PAYLOAD_NAMES = list(
    garak.payloads.Loadmaster().search()
)  # default includes local custom payloads to help test them


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_core_payloads(payload_name):
    f = garak.payloads.Loadmaster()
    p = f.get(payload_name)
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
    f = garak.payloads.Loadmaster()
    assert isinstance(f, garak.payloads.Loadmaster)


def test_payload_list():
    f = garak.payloads.Loadmaster()
    for payload_name in f.search():
        assert isinstance(
            payload_name, str
        ), "Payload names from Loadmaster().search() must be strings"


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_payloads_have_valid_tags(payload_name, payload_typology):
    f = garak.payloads.Loadmaster()
    p = f.get(payload_name)
    for typee in p.types:
        assert (
            typee in payload_typology
        ), f"Payload {payload_name} type {typee} not found in payload typology"
