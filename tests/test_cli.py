#!/usr/bin/env python3

from garak import __version__, cli

def test_version_command(capsys):
    cli.main(['--version'])
    result = capsys.readouterr()
    assert "garak" in result.out
    assert f"v{__version__}" in result.out
    assert len(result.out.strip().split("\n")) == 1
