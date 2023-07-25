#!/usr/bin/env python3

import os
from pathlib import Path
import pytest

top_paths = ["probes", "detectors", "harnesses", "generators", "evaluators"]
m = {}
for top_path in top_paths:
    m[top_path] = [
        str(i).split("/")[2].replace(".py", "")
        for i in Path(f"garak/{top_path}").glob("*py")
        if not str(i).endswith("__init__.py")
    ]


@pytest.mark.parametrize("category", top_paths)
def test_top_docs(category):
    file_path = f"docs/source/garak.{category}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["probes"])
def test_docs_probes(classname):
    file_path = f"docs/source/garak.probes.{classname}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["detectors"])
def test_docs_detectors(classname):
    file_path = f"docs/source/garak.detectors.{classname}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["harnesses"])
def test_docs_harnesses(classname):
    file_path = f"docs/source/garak.harnesses.{classname}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["evaluators"])
def test_docs_evaluators(classname):
    file_path = f"docs/source/garak.evaluators.{classname}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["generators"])
def test_docs_generators(classname):
    file_path = f"docs/source/garak.generators.{classname}.rst"
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
