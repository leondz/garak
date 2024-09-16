# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
import tempfile
import os

from garak import _config
from garak.exception import GarakException
from garak.data import path as data_path
from garak.data import LocalDataPath


@pytest.fixture
def random_resource_filename(request) -> None:
    with tempfile.NamedTemporaryFile(
        dir=LocalDataPath.ORDERED_SEARCH_PATHS[-1], mode="w", delete=False
    ) as tmpfile:
        tmpfile.write("file data")

    def remove_files():
        for path in LocalDataPath.ORDERED_SEARCH_PATHS:
            rem_path = path / os.path.basename(tmpfile.name)
            if rem_path.exists():
                rem_path.unlink()

    request.addfinalizer(remove_files)

    return os.path.basename(tmpfile.name)


def test_no_relative_escape():
    with pytest.raises(GarakException) as exc_info:
        data_path / ".."
    assert "does not refer to a valid path" in str(exc_info.value)


def test_no_relative_escape_extended():
    autodan_path = data_path / "autodan"
    with pytest.raises(GarakException) as exc_info:
        autodan_path / ".." / ".." / "configs"
    assert "does not refer to a valid path" in str(exc_info.value)


def test_allow_relative_in_path():
    source = data_path / "autodan" / ".." / "gcg"
    assert source.name == "gcg"


def test_known_resource_found():
    known_filename = "misp_descriptions.tsv"
    source = data_path / known_filename
    assert source.name == known_filename


def test_local_override(random_resource_filename):
    source = data_path / random_resource_filename
    assert _config.transient.package_dir in source.parents

    data_root_path = _config.transient.data_dir / "resources"
    data_root_path.mkdir(parents=True, exist_ok=True)
    with open(
        data_root_path / random_resource_filename, encoding="utf-8", mode="w"
    ) as f:
        f.write("fake data")

    source = data_path / random_resource_filename
    assert _config.transient.data_dir in source.parents
