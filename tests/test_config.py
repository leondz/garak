#!/usr/bin/env python3

import json
import pytest
import os
import re
import tempfile

from garak import _config
import garak.cli
from garak.command import list_config

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

options_solo = [
    #    "verbose", # not sure hot to test argparse action="count"
    #    "deprefix", # this param is weird
    "narrow_output",
    "extended_detectors",
]
options_param = [
    ("report_prefix", "laurelhurst"),
    ("parallel_requests", 9),
    ("parallel_attempts", 9),
    ("seed", 9001),
    ("eval_threshold", 0.9),
    ("generations", 9),
    #    ("config", "obsidian.yaml"), # optional config file names passed via CLI don't get stored in _config. that'll suck to troubleshoot
    ("model_type", "test"),
    ("model_name", "bruce"),
]
options_spec = [
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
@pytest.mark.parametrize("option", options_solo)
def test_cli_solo_settings(option):
    garak.cli.main(
        [f"--{option}", "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    assert getattr(subconfig, option) == True


@pytest.mark.parametrize("param", options_param)
def test_cli_param_settings(param):
    option, value = param
    garak.cli.main(
        [f"--{option}", str(value), "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    if option == "report_prefix":
        os.remove(f"{value}.report.jsonl")
    assert getattr(subconfig, option) == value


@pytest.mark.parametrize("param", options_spec)
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


# test that run YAML overrides core YAML
@pytest.mark.parametrize("param", options_param)
def test_yaml_param_settings(param):
    option, value = param
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(f"---\n{param_locs[option]}:\n  {option}: {value}\n".encode("utf-8"))
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        subconfig = getattr(_config, param_locs[option])
        assert getattr(subconfig, option) == value


# # test that site YAML overrides core YAML # needs file staging for site yaml
def test_site_yaml_overrides_core_yaml():
    assert False


# # test that run YAML overrides site YAML # needs file staging for site yaml
def test_run_yaml_overrides_site_yaml():
    assert False


# test that CLI config overrides run YAML
def test_cli_overrides_run_yaml():
    orig_seed = 10101
    override_seed = 37176
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(f"---\nrun:\n  seed: {orig_seed}\n".encode("utf-8"))
        garak.cli.main(
            ["--config", tmp.name, "-s", f"{override_seed}", "--list_config"]
        )  # add list_config as the action so we don't actually run
        assert _config.run.seed == override_seed


# test probe_options YAML
def test_probe_options_yaml(capsys):
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(
            """
---
plugins:
  probe_spec: test.Blank
  probe_options:
    test.Blank:    
        gen_x: 37176
""".encode(
                "utf-8"
            )
        )
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        print(_config.plugins.probe_options)
        assert _config.plugins.probe_options["test.Blank"]["gen_x"] == 37176


# test generator_options YAML
def test_generator_options_yaml(capsys):
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(
            "---\nplugins:\n  model_type: test.Blank\n  probe_spec: test.Blank\n  generator_options:\n    gen_x: 37176\n".encode(
                "utf-8"
            )
        )
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        assert _config.plugins.generator_options["gen_x"] == 37176


# can a run be launched from a run YAML?
def test_run_from_yaml(capsys):
    with tempfile.NamedTemporaryFile(buffering=0) as tmp:
        tmp.write(
            "---\nrun:\n  generations: 10\n\nplugins:\n  model_type: test.Blank\n  probe_spec: test.Blank\n".encode(
                "utf-8"
            )
        )
        garak.cli.main(["--config", tmp.name])
    result = capsys.readouterr()
    output = result.out
    all_output = ""
    for line in output.strip().split("\n"):
        line = ansi_escape.sub("", line)
        all_output += line

    assert "loading generator: Test: Blank" in all_output
    assert "queue of probes: test.Blank" in all_output
    assert "ok on   10/  10" in all_output
    assert "always.Pass:" in all_output
    assert "test.Blank" in all_output
    assert "garak done: complete" in all_output


# cli generator options file loads
def test_cli_generator_options_file():
    # write an options file
    with tempfile.NamedTemporaryFile(mode="w+") as tmp:
        json.dump({"test.Blank": {"this_is_a": "generator"}}, tmp)
        tmp.flush()
        # invoke cli
        garak.cli.main(
            ["--generator_option_file", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run

        # check it was loaded
        print(_config.plugins.generator_options)
        assert _config.plugins.generator_options["test.Blank"] == {
            "this_is_a": "generator"
        }


# cli generator options file loads
def test_cli_probe_options_file():
    # write an options file
    with tempfile.NamedTemporaryFile(mode="w+") as tmp:
        json.dump({"test.Blank": {"probes_in_this_config": 1}}, tmp)
        tmp.flush()
        # invoke cli
        garak.cli.main(
            ["--probe_option_file", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run

        # check it was loaded
        print(_config.plugins.probe_options)
        assert _config.plugins.probe_options["test.Blank"] == {
            "probes_in_this_config": 1
        }


# cli probe config file overrides yaml probe config (using combine into)
def test_cli_probe_options_overrides_yaml_probe_options():
    assert False


# check that probe picks up yaml config items
def test_blank_probe_instance_loads_yaml_config():
    assert False


# check that probe picks up cli config items
def test_blank_probe_instance_loads_cli_config():
    probe_name = "test.Blank"
    revised_goal = "make the model forget what to output"
    garak.cli.main(
        [
            "-p",
            probe_name,
            "--probe_options",
            json.dumps({probe_name: {"goal": revised_goal}}),
        ]
    )
    probe = garak._plugins.load_plugin(f"probes.{probe_name}")
    assert probe.goal == revised_goal


# check that generator picks up config items
def test_blank_generator_instance_loads_config():
    assert False


# test parsing of probespec
def test_probespec_loading():
    assert False
