import importlib
import os
from pathlib import Path
import pytest

top_paths = ["probes", "detectors", "harnesses", "generators", "evaluators", "buffs"]
doc_source = os.path.join("docs", "source")

m = {}
for top_path in top_paths:
    m[top_path] = [
        str(i).split(os.sep)[2].replace(".py", "")
        for i in Path(f"garak{os.sep}{top_path}").glob("*py")
        if not str(i).endswith("__init__.py")
    ]


@pytest.mark.parametrize("category", top_paths)
def test_top_docs(category):
    file_path = os.path.join(doc_source, f"garak.{category}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0


@pytest.mark.parametrize("classname", m["probes"])
def test_docs_probes(classname):
    file_path = os.path.join(doc_source, f"garak.probes.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, "probes.rst")
    target_doc = f"garak.probes.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # probe docs must be linked to in probes.rst


@pytest.mark.parametrize("classname", m["detectors"])
def test_docs_detectors(classname):
    file_path = os.path.join(doc_source, f"garak.detectors.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, f"detectors.rst")
    target_doc = f"garak.detectors.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # detector docs must be linked to in detectors.rst


@pytest.mark.parametrize("classname", m["harnesses"])
def test_docs_harnesses(classname):
    file_path = os.path.join(doc_source, f"garak.harnesses.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, f"harnesses.rst")
    target_doc = f"garak.harnesses.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # harness docs must be linked to in harnesses.rst


@pytest.mark.parametrize("classname", m["evaluators"])
def test_docs_evaluators(classname):
    file_path = os.path.join(doc_source, f"garak.evaluators.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, "evaluators.rst")
    target_doc = f"garak.evaluators.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # evaluator docs must be linked to in evaluators.rst


@pytest.mark.parametrize("classname", m["generators"])
def test_docs_generators(classname):
    file_path = os.path.join(doc_source, f"garak.generators.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, f"generators.rst")
    target_doc = f"garak.generators.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # generator docs must be linked to in generators.rst


@pytest.mark.parametrize("classname", m["buffs"])
def test_docs_generators(classname):
    file_path = os.path.join(doc_source, f"garak.buffs.{classname}.rst")
    assert os.path.isfile(file_path)
    assert os.path.getsize(file_path) > 0
    category_file = os.path.join(doc_source, f"buffs.rst")
    target_doc = f"garak.buffs.{classname}\n"
    assert (
        open(category_file, "r", encoding="utf-8").read().find(target_doc) != -1
    )  # buff docs must be linked to in buffs.rst


from garak import _plugins

probes = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]
detectors = [
    classname for (classname, active) in _plugins.enumerate_plugins("detectors")
]
generators = [
    classname for (classname, active) in _plugins.enumerate_plugins("generators")
]
harnesses = [
    classname for (classname, active) in _plugins.enumerate_plugins("harnesses")
]
buffs = [classname for (classname, active) in _plugins.enumerate_plugins("buffs")]
# commented out until enumerate_plugins supports evaluators
# evaluators = [
#    classname for (classname, active) in _plugins.enumerate_plugins("evaluators")
# ]
plugins = probes + detectors + generators + buffs


@pytest.mark.parametrize("plugin_name", plugins)
def test_check_docstring(plugin_name):
    plugin_name_parts = plugin_name.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    doc = getattr(getattr(mod, class_name), "__doc__")
    assert isinstance(doc, str)
    assert len(doc) > 0
