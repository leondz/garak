# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable
import importlib
import tempfile

import pytest

import garak._config
import garak._plugins
import garak.attempt
import garak.generators.test

# probes should be able to return a generator of attempts
# -> probes.base.Probe._execute_all (1) should be able to consume a generator of attempts
# generators should be able to return a generator of outputs
# -> attempts (2) should be able to consume a generator of outputs
# -> detectors (3) should be able to consume a generator of outputs
# detectors should be able to return generators of results
# -> evaluators (4) should be able to consume generators of results
# -> attempts (5) should be able to consume generators of detector results
# -> attempt.as_dict (6) should be able to relay a generator of detector results


@pytest.fixture(autouse=True)
def _config_loaded():
    importlib.reload(garak._config)
    garak._config.load_base_config()
    temp_report_file = tempfile.NamedTemporaryFile(mode="w+")
    garak._config.transient.reportfile = temp_report_file
    garak._config.transient.report_filename = temp_report_file.name
    yield
    temp_report_file.close()


def test_generator_consume_attempt_generator():
    count = 5
    attempts = (garak.attempt.Attempt(prompt=str(i)) for i in range(count))
    p = garak._plugins.load_plugin("probes.test.Blank")
    g = garak._plugins.load_plugin("generators.test.Blank")
    p.generator = g
    results = p._execute_all(attempts)

    assert isinstance(results, Iterable), "_execute_all should return an Iterable"
    result_len = 0
    for _attempt in results:
        assert isinstance(
            _attempt, garak.attempt.Attempt
        ), "_execute_all should return attempts"
        result_len += 1
    assert (
        result_len == count
    ), "there should be the same number of attempts in the passed generator as results returned in _execute_all"
