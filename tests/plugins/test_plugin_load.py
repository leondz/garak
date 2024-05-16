import pytest

import garak
from garak import _plugins

PROBES = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]

DETECTORS = [
    classname for (classname, active) in _plugins.enumerate_plugins("detectors")
]

HARNESSES = [
    classname for (classname, active) in _plugins.enumerate_plugins("harnesses")
]

BUFFS = [classname for (classname, active) in _plugins.enumerate_plugins("buffs")]


@pytest.mark.parametrize("classname", PROBES)
def test_instantiate_probes(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.probes.base.Probe)


@pytest.mark.parametrize("classname", DETECTORS)
def test_instantiate_detectors(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.detectors.base.Detector)


@pytest.mark.parametrize("classname", HARNESSES)
def test_instantiate_harnesses(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.harnesses.base.Harness)


@pytest.mark.parametrize("classname", BUFFS)
def test_instantiate_harnesses(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.buffs.base.Buff)
