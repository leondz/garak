# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import csv

import pytest

import garak._config
import garak.payloads


def test_payload_finder():
    f = garak.payloads.Finder()
    assert isinstance(f, garak.payloads.Finder)


def test_payload_list():
    f = garak.payloads.Finder()
    for payload_name in f.select():
        assert isinstance(
            payload_name, str
        ), "Payload names from Finder().select() must be strings"


PAYLOAD_NAMES = list(
    garak.payloads.Finder().select()
)  # default includes local custom payloads to help test them


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_core_payloads(payload_name):
    f = garak.payloads.Finder()
    p = f.get(payload_name)
    assert isinstance(
        p, garak.payloads.PayloadGroup
    ), f"Not a valid payload: {payload_name}"


@pytest.fixture(scope="module", autouse=True)
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


@pytest.mark.parametrize("payload_name", PAYLOAD_NAMES)
def test_payloads_have_valid_tags(payload_name, payload_typology):
    f = garak.payloads.Finder()
    p = f.get(payload_name)
    for typee in p.types:
        assert (
            typee in payload_typology
        ), f"Payload {payload_name} type {typee} not found in payload typology"
