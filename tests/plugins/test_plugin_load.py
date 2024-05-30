import pytest
import os

import garak
from garak import _plugins
import garak.generators

PROBES = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]

DETECTORS = [
    classname for (classname, active) in _plugins.enumerate_plugins("detectors")
]

HARNESSES = [
    classname for (classname, active) in _plugins.enumerate_plugins("harnesses")
]

BUFFS = [classname for (classname, active) in _plugins.enumerate_plugins("buffs")]

GENERATORS = [
    "generators.test.Blank"
]  # generator options are complex, hardcode test.Blank only for now


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
def test_instantiate_buffs(classname):
    g = _plugins.load_plugin(classname)
    assert isinstance(g, garak.buffs.base.Buff)


@pytest.mark.parametrize("classname", GENERATORS)
def test_instantiate_generators(classname):
    category, namespace, klass = classname.split(".")
    from garak._config import GarakSubConfig

    gen_config = {
        namespace: {
            klass: {
                "name": "gpt-3.5-turbo-instruct",  # valid for OpenAI
            }
        }
    }
    config_root = GarakSubConfig()
    setattr(config_root, category, gen_config)

    g = _plugins.load_plugin(classname, config_root=config_root)
    assert isinstance(g, garak.generators.base.Generator)
