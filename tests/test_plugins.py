#!/usr/bin/env python3

import os
import pytest

import garak.generators
from garak import _plugins

# NB excludes generators

probes = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]


@pytest.mark.parametrize("classname", probes)
def test_instantiate_probes(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.probes.base.Probe)


detectors = [
    classname for (classname, active) in _plugins.enumerate_plugins("detectors")
]


@pytest.mark.parametrize("classname", detectors)
def test_instantiate_detectors(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.detectors.base.Detector)


harnesses = [
    classname for (classname, active) in _plugins.enumerate_plugins("harnesses")
]


@pytest.mark.parametrize("classname", harnesses)
def test_instantiate_harnesses(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.harnesses.base.Harness)
