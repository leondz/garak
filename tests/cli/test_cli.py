import re
import pytest
import os

from garak import __version__, cli, _config

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@pytest.fixture(autouse=True)
def close_report_file():
    if _config.transient.reportfile is not None:
        _config.transient.reportfile.close()
        if os.path.exists(_config.transient.report_filename):
            os.remove(_config.transient.report_filename)


def test_version_command(capsys):
    cli.main(["--version"])
    result = capsys.readouterr()
    output = ansi_escape.sub("", result.out)
    assert "garak" in output
    assert f"v{__version__}" in output
    assert len(output.strip().split("\n")) == 1


def test_probe_list(capsys):
    cli.main(["--list_probes"])
    result = capsys.readouterr()
    output = ansi_escape.sub("", result.out)
    for line in output.strip().split("\n"):
        assert re.match(
            r"^probes: [a-z0-9_]+(\.[A-Za-z0-9_]+)?( 🌟)?( 💤)?$", line
        ) or line.startswith("garak LLM security probe v")


def test_detector_list(capsys):
    cli.main(["--list_detectors"])
    result = capsys.readouterr()
    output = ansi_escape.sub("", result.out)
    for line in output.strip().split("\n"):
        assert re.match(
            r"^detectors: [a-z0-9_]+(\.[A-Za-z0-9_]+)?( 🌟)?( 💤)?$", line
        ) or line.startswith("garak LLM security probe v")


def test_generator_list(capsys):
    cli.main(["--list_generators"])
    result = capsys.readouterr()
    output = ansi_escape.sub("", result.out)
    for line in output.strip().split("\n"):
        assert re.match(
            r"^generators: [a-z0-9_]+(\.[A-Za-z0-9_]+)?( 🌟)?( 💤)?$", line
        ) or line.startswith("garak LLM security probe v")


def test_buff_list(capsys):
    cli.main(["--list_buffs"])
    result = capsys.readouterr()
    output = ansi_escape.sub("", result.out)
    for line in output.strip().split("\n"):
        assert re.match(
            r"^buffs: [a-z0-9_]+(\.[A-Za-z0-9_]+)?( 🌟)?( 💤)?$", line
        ) or line.startswith("garak LLM security probe v")


def test_run_all_probes(capsys):
    cli.main(["-m", "test", "-p", "all", "-d", "always.Pass", "-g", "1"])
    result = capsys.readouterr()
    last_line = result.out.strip().split("\n")[-1]
    assert re.match("^✔️  garak run complete in [0-9]+\\.[0-9]+s$", last_line)


def test_run_all_detectors(capsys):
    cli.main(["-m", "test", "-p", "blank.BlankPrompt", "-d", "all", "-g", "1"])
    result = capsys.readouterr()
    last_line = result.out.strip().split("\n")[-1]
    assert re.match("^✔️  garak run complete in [0-9]+\\.[0-9]+s$", last_line)
