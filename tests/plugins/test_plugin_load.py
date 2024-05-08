import pytest

import garak
from garak import _plugins

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


buffs = [classname for (classname, active) in _plugins.enumerate_plugins("buffs")]


@pytest.mark.parametrize("classname", buffs)
def test_instantiate_harnesses(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.buffs.base.Buff)
