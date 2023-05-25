#!/usr/bin/env python3

import re

from garak import __version__, cli


def test_version_command(capsys):
    cli.main(["--version"])
    result = capsys.readouterr()
    assert "garak" in result.out
    assert f"v{__version__}" in result.out
    assert len(result.out.strip().split("\n")) == 1


def test_probe_list(capsys):
    cli.main(["--list_probes"])
    result = capsys.readouterr()
    for line in result.out.strip().split("\n"):
        assert re.match(r"^probes.[a-z0-9_]+.[A-Za-z0-9_]+$", line)


def test_detector_list(capsys):
    cli.main(["--list_detectors"])
    result = capsys.readouterr()
    for line in result.out.strip().split("\n"):
        assert re.match(r"^detectors.[a-z0-9_]+.[A-Za-z0-9_]+$", line)


def test_generator_list(capsys):
    cli.main(["--list_generators"])
    result = capsys.readouterr()
    for line in result.out.strip().split("\n"):
        assert re.match(r"^generators.[a-z0-9_]+.[A-Za-z0-9_]+$", line)
