# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import json
import os
import re
import shutil
import tempfile

import pytest

from garak import _config
import garak.cli


site_yaml_filename = "TESTONLY.site.yaml.bak"

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
for p in _config.reporting_params:
    param_locs[p] = "reporting"


# test CLI assertions of each var
@pytest.mark.parametrize("option", options_solo)
def test_cli_solo_settings(option):
    importlib.reload(_config)

    garak.cli.main(
        [f"--{option}", "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    assert getattr(subconfig, option) == True


@pytest.mark.parametrize("param", options_param)
def test_cli_param_settings(param):
    importlib.reload(_config)

    option, value = param
    garak.cli.main(
        [f"--{option}", str(value), "--list_config"]
    )  # add list_config as the action so we don't actually run
    subconfig = getattr(_config, param_locs[option])
    assert getattr(subconfig, option) == value


@pytest.mark.parametrize("param", options_spec)
def test_cli_spec_settings(param):
    importlib.reload(_config)

    option, value, configname = param
    garak.cli.main(
        [f"--{option}", str(value), "--list_config"]
    )  # add list_config as the action so we don't actually run
    assert getattr(_config.plugins, configname) == value


# test a short-form CLI assertion
def test_cli_shortform():
    importlib.reload(_config)

    garak.cli.main(["-s", "444", "--list_config"])
    assert _config.run.seed == 444
    if _config.transient.reportfile is not None:
        _config.transient.reportfile.close()
        if os.path.exists(_config.transient.report_filename):
            os.remove(_config.transient.report_filename)

    garak.cli.main(
        ["-g", "444", "--list_config"]
    )  # seed gets special treatment, try another
    assert _config.run.generations == 444


# test that run YAML overrides core YAML
@pytest.mark.parametrize("param", options_param)
def test_yaml_param_settings(param):
    importlib.reload(_config)

    option, value = param
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(f"---\n{param_locs[option]}:\n  {option}: {value}\n".encode("utf-8"))
        tmp.close()
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        subconfig = getattr(_config, param_locs[option])
        os.remove(tmp.name)
        assert getattr(subconfig, option) == value


# # test that site YAML overrides core YAML # needs file staging for site yaml
def test_site_yaml_overrides_core_yaml():
    importlib.reload(_config)

    site_cfg_moved = False
    try:
        shutil.move("garak/garak.site.yaml", site_yaml_filename)
        site_cfg_moved = True
    except FileNotFoundError:
        site_cfg_moved = False

    with open("garak/garak.site.yaml", "w", encoding="utf-8") as f:
        f.write("---\nrun:\n  eval_threshold: 0.777\n")
        f.flush()
        garak.cli.main(["--list_config"])

    if site_cfg_moved:
        shutil.move(site_yaml_filename, "garak/garak.site.yaml")
    else:
        os.remove("garak/garak.site.yaml")

    assert _config.run.eval_threshold == 0.777


# # test that run YAML overrides site YAML # needs file staging for site yaml
def test_run_yaml_overrides_site_yaml():
    importlib.reload(_config)

    site_cfg_moved = False
    try:
        shutil.move("garak/garak.site.yaml", site_yaml_filename)
        site_cfg_moved = True
    except FileNotFoundError:
        site_cfg_moved = False

    with open("garak/garak.site.yaml", "w", encoding="utf-8") as f:
        f.write("---\nrun:\n  eval_threshold: 0.777\n")
        f.flush()
        garak.cli.main(["--list_config", "--eval_threshold", str(0.9001)])

    if site_cfg_moved:
        shutil.move(site_yaml_filename, "garak/garak.site.yaml")
    else:
        os.remove("garak/garak.site.yaml")

    assert _config.run.eval_threshold == 0.9001


# test that CLI config overrides run YAML
def test_cli_overrides_run_yaml():
    importlib.reload(_config)

    orig_seed = 10101
    override_seed = 37176
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(f"---\nrun:\n  seed: {orig_seed}\n".encode("utf-8"))
        tmp.close()
        garak.cli.main(
            ["--config", tmp.name, "-s", f"{override_seed}", "--list_config"]
        )  # add list_config as the action so we don't actually run
        os.remove(tmp.name)
        assert _config.run.seed == override_seed


# test probe_options YAML
def test_probe_options_yaml(capsys):
    importlib.reload(_config)

    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(
            """
---
plugins:
  probe_spec: test.Blank
  probes:
    test.Blank:    
        gen_x: 37176
""".encode(
                "utf-8"
            )
        )
        tmp.close()
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        os.remove(tmp.name)
        assert _config.plugins.probes["test.Blank"]["gen_x"] == 37176


# test generator_options YAML
def test_generator_options_yaml(capsys):
    importlib.reload(_config)

    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(
            "---\nplugins:\n  model_type: test.Blank\n  probe_spec: test.Blank\n  generators:\n    test.Blank:\n      gen_x: 37176\n".encode(
                "utf-8"
            )
        )
        tmp.close()
        garak.cli.main(
            ["--config", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        os.remove(tmp.name)
        assert _config.plugins.generators["test.Blank"]["gen_x"] == 37176


# can a run be launched from a run YAML?
def test_run_from_yaml(capsys):
    importlib.reload(_config)

    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(
            "---\nrun:\n  generations: 10\n\nplugins:\n  model_type: test.Blank\n  probe_spec: test.Blank\n".encode(
                "utf-8"
            )
        )
        tmp.close()
        garak.cli.main(["--config", tmp.name])
        os.remove(tmp.name)
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
    assert "garak run complete" in all_output


# cli generator options file loads
def test_cli_generator_options_file():
    importlib.reload(_config)

    # write an options file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        json.dump({"test.Blank": {"this_is_a": "generator"}}, tmp)
        tmp.close()
        # invoke cli
        garak.cli.main(
            ["--generator_option_file", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        os.remove(tmp.name)

        # check it was loaded
        assert _config.plugins.generators["test.Blank"] == {"this_is_a": "generator"}


# cli generator options file loads
def test_cli_probe_options_file():
    importlib.reload(_config)

    # write an options file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        json.dump({"test.Blank": {"probes_in_this_config": 1}}, tmp)
        tmp.close()
        # invoke cli
        garak.cli.main(
            ["--probe_option_file", tmp.name, "--list_config"]
        )  # add list_config as the action so we don't actually run
        os.remove(tmp.name)

        # check it was loaded
        assert _config.plugins.probes["test.Blank"] == {"probes_in_this_config": 1}


# cli probe config file overrides yaml probe config (using combine into)
def test_cli_probe_options_overrides_yaml_probe_options():
    importlib.reload(_config)

    # write an options file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as probe_json_file:
        json.dump({"test.Blank": {"goal": "taken from CLI JSON"}}, probe_json_file)
        probe_json_file.close()
        with tempfile.NamedTemporaryFile(buffering=0, delete=False) as probe_yaml_file:
            probe_yaml_file.write(
                """
---
plugins:
    probes:
        test.Blank:
            goal: taken from CLI YAML
""".encode(
                    "utf-8"
                )
            )
            probe_yaml_file.close()
            # invoke cli
            garak.cli.main(
                [
                    "--config",
                    probe_yaml_file.name,
                    "--probe_option_file",
                    probe_json_file.name,
                    "--list_config",
                ]
            )  # add list_config as the action so we don't actually run
            os.remove(probe_json_file.name)
            os.remove(probe_yaml_file.name)
        # check it was loaded
        assert _config.plugins.probes["test.Blank"]["goal"] == "taken from CLI JSON"


# cli should override yaml options
def test_cli_generator_options_overrides_yaml_probe_options():
    importlib.reload(_config)

    cli_generations_count = 9001
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as generator_yaml_file:
        generator_yaml_file.write(
            """
---
run:
    generations: 999
""".encode(
                "utf-8"
            )
        )
        generator_yaml_file.close()
        args = [
            "--config",
            generator_yaml_file.name,
            "-g",
            str(cli_generations_count),
            "--list_config",
        ]  # add list_config as the action so we don't actually run
        print(args)
        garak.cli.main(args)
        os.remove(generator_yaml_file.name)
    # check it was loaded
    assert _config.run.generations == cli_generations_count


# check that probe picks up yaml config items
def test_blank_probe_instance_loads_yaml_config():
    importlib.reload(_config)

    probe_name = "test.Blank"
    revised_goal = "TEST GOAL make the model forget what to output"
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(
            f"---\nplugins:\n  probes:\n    {probe_name}:\n      goal: {revised_goal}\n".encode(
                "utf-8"
            )
        )
        tmp.close()
        garak.cli.main(["--config", tmp.name, "-p", probe_name])
        os.remove(tmp.name)
    probe = garak._plugins.load_plugin(f"probes.{probe_name}")
    assert probe.goal == revised_goal


# check that probe picks up cli config items
def test_blank_probe_instance_loads_cli_config():
    importlib.reload(_config)

    probe_name = "test.Blank"
    revised_goal = "TEST GOAL make the model forget what to output"
    args = [
        "-p",
        probe_name,
        "--probe_options",
        json.dumps({probe_name: {"goal": revised_goal}}),
    ]
    garak.cli.main(args)
    probe = garak._plugins.load_plugin(f"probes.{probe_name}")
    assert probe.goal == revised_goal


# check that generator picks up yaml config items
def test_blank_generator_instance_loads_yaml_config():
    importlib.reload(_config)

    generator_name = "test.Blank"
    revised_temp = 0.9001
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        tmp.write(
            f"---\nplugins:\n  generators:\n    {generator_name}:\n      temperature: {revised_temp}\n".encode(
                "utf-8"
            )
        )
        tmp.close()
        garak.cli.main(
            ["--config", tmp.name, "--model_type", generator_name, "--probes", "none"]
        )
        os.remove(tmp.name)
    gen = garak._plugins.load_plugin(f"generators.{generator_name}")
    assert gen.temperature == revised_temp


# check that generator picks up cli config items
def test_blank_generator_instance_loads_cli_config():
    importlib.reload(_config)

    generator_name = "test.Repeat"
    revised_temp = 0.9001
    args = [
        "--model_type",
        "test.Blank",
        "--probes",
        "none",
        "--generator_options",
        json.dumps({generator_name: {"temperature": revised_temp}})
        .replace(" ", "")
        .strip(),
    ]
    garak.cli.main(args)
    gen = garak._plugins.load_plugin(f"generators.{generator_name}")
    assert gen.temperature == revised_temp


# test parsing of probespec
def test_probespec_loading():
    assert _config.parse_plugin_spec(None, "detectors") == []
    assert _config.parse_plugin_spec("Auto", "probes") == []
    assert _config.parse_plugin_spec("NONE", "probes") == []
    assert _config.parse_plugin_spec("", "generators") == []
    assert _config.parse_plugin_spec("atkgen", "probes") == ["probes.atkgen.Tox"]
    assert _config.parse_plugin_spec(
        "long.test.class,another.long.test.class", "probes"
    ) == ["probes.long.test.class", "probes.another.long.test.class"]
    assert _config.parse_plugin_spec("always", "detectors") == [
        "detectors.always.Fail",
        "detectors.always.Pass",
    ]


def test_buff_config_assertion():
    importlib.reload(_config)
    import garak._plugins

    test_value = 9001
    _config.plugins.buffs["paraphrase.Fast"] = {"num_beams": test_value}
    p = garak._plugins.load_plugin("buffs.paraphrase.Fast")
    assert p.num_beams == test_value


def test_tag_filter():
    assert (
        _config.parse_plugin_spec("atkgen", "probes", probe_tag_filter="LOL NULL") == []
    )
    assert _config.parse_plugin_spec("*", "probes", probe_tag_filter="avid") != []
    assert (
        _config.parse_plugin_spec("all", "probes", probe_tag_filter="owasp:llm") != []
    )
    assert "probes.lmrc.SexualContent" in _config.parse_plugin_spec(
        "all", "probes", probe_tag_filter="risk-cards:lmrc:sexual_content"
    )


def test_report_prefix_with_hitlog_no_explode():
    importlib.reload(_config)

    garak.cli.main(
        "-m test.Blank --report_prefix kjsfhgkjahpsfdg -p test.Blank -d always.Fail".split()
    )
    assert os.path.isfile("kjsfhgkjahpsfdg.report.jsonl")
    assert os.path.isfile("kjsfhgkjahpsfdg.report.html")
    assert os.path.isfile("kjsfhgkjahpsfdg.hitlog.jsonl")


@pytest.fixture(autouse=True)
def cleanup(request):
    """Cleanup a testing and report directory once we are finished."""

    def remove_log_files():
        files = [
            "laurelhurst.report.jsonl",
            "kjsfhgkjahpsfdg.report.jsonl",
            "kjsfhgkjahpsfdg.report.html",
            "kjsfhgkjahpsfdg.hitlog.jsonl",
        ]
        if _config.transient.reportfile is not None:
            _config.transient.reportfile.close()
            files.append(_config.transient.report_filename)

        for file in files:
            if os.path.exists(file):
                os.remove(file)

    request.addfinalizer(remove_log_files)
