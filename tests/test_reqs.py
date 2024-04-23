# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

try:
    import tomllib
except:
    tomllib = None


@pytest.mark.skipif(
    tomllib is None, reason="No tomllib found (available from Python 3.11)"
)
def test_requirements_txt_pyproject_toml():
    with open("requirements.txt", "r", encoding="utf-8") as req_file:
        reqtxt_reqs = req_file.readlines()
        reqtxt_reqs = list(
            filter(lambda x: not x.startswith("#"), map(str.strip, reqtxt_reqs))
        )
        reqtxt_reqs.sort()
    with open("pyproject.toml", "rb") as pyproject_file:
        pyproject_toml = tomllib.load(pyproject_file)
        pyproject_reqs = pyproject_toml["project"]["dependencies"]
        for test_deps in pyproject_toml["project"]["optional-dependencies"].values():
            for dep in test_deps:
                pyproject_reqs.append(dep)
        pyproject_reqs.sort()
    # assert len(reqtxt_reqs) == len(pyproject_reqs) # same number of requirements
    assert (
        set(reqtxt_reqs) - set(pyproject_reqs) == set()
    )  # things in reqtxt but not in pyproject
    assert (
        set(pyproject_reqs) - set(reqtxt_reqs) == set()
    )  # things in pyproject but not in reqtxt
    assert (
        reqtxt_reqs == pyproject_reqs
    )  # final check. this one is actually enough, but let's help us debug by finding which test fails, ok?
