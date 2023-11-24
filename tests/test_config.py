#!/usr/bin/env python3

import pytest
import tempfile

from garak import _config
import garak.cli


cli_options_solo = [
    #    "verbose", # not sure hot to test argparse action="count"
    #    "deprefix", # this param is weird
    "narrow_output",
    "extended_detectors",
]
cli_options_param = [
    ("report_prefix", "laurelhurst"),
    ("parallel_requests", 9),
    ("parallel_attempts", 9),
    ("seed", 9001),
    ("eval_threshold", 0.9),
    ("generations", 9),
    #    ("config", "obsidian.yaml"), # this doesn't get stored in _config. that'll suck to troubleshoot
    ("model_type", "test"),
    ("model_name", "bruce"),
]
cli_options_spec = [
    ("probes", "3,elim,gul.dukat", "probe_spec"),
    ("detectors", "all", "detector_spec"),
    ("buff", "polymorph", "buff_spec"),
]

param_locs = {}
for p in _config.system_params:
    param_locs[p] = "system"
for p in _config.run_params:
    param_locs[p] = "run"
for p in _config.plugins_params:
    param_locs[p] = "plugins"


# test CLI assertions of each var
@pytest.mark.parametrize("option", cli_options_solo)
def test_cli_solo_settings(option):
    garak.cli.main(
        [f"--{option}", "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    assert getattr(subconfig, option) == True


@pytest.mark.parametrize("param", cli_options_param)
def test_cli_param_settings(param):
    option, value = param
    garak.cli.main(
        [f"--{option}", str(value), "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    assert getattr(subconfig, option) == value


@pytest.mark.parametrize("param", cli_options_spec)
def test_cli_spec_settings(param):
    option, value, configname = param
    garak.cli.main(
        [f"--{option}", str(value), "--list_config"]
    )  # add list_config as the action so we don't actually run
    assert getattr(_config.plugins, configname) == value


# test a short-form CLI assertion
def test_cli_shortform():
    garak.cli.main(["-s", "444", "--list_config"])
    assert _config.run.seed == 444
    garak.cli.main(
        ["-g", "444", "--list_config"]
    )  # seed gets special treatment, try another
    assert _config.run.generations == 444


# test YAML assertions of param/value tuple vars
@pytest.mark.parametrize("param", cli_options_param)
def test_yaml_param_settings(param):
    option, value = param
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(f"---\n{param_locs[option]}:\n  {option}: {value}\n".encode("utf-8"))
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        subconfig = getattr(_config, param_locs[option])
        assert getattr(subconfig, option) == value


# # test that site YAML overrides core YAML # needs file staging
# test that run YAML overrides core YAML
# test that run YAML overrides core YAML
# # test that run YAML overrides site YAML # needs file staging
# test that CLI config overrides run YAML
# test probe_options YAML
# test generator_options YAML
# can a run be launched from a run YAML?
