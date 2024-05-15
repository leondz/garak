import importlib
import pytest

from garak import _plugins

probes = [classname for (classname, active) in _plugins.enumerate_plugins("probes")]
detectors = [
    classname
    for (classname, active) in _plugins.enumerate_plugins(
        "detectors", skip_base_classes=False
    )
]
detector_bare_names = [".".join(d.split(".")[1:]) for d in detectors]


@pytest.mark.parametrize("classname", probes)
def test_detector_specified(classname):  # every probe should give detector(s)
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    assert (
        isinstance(probe_class.primary_detector, str)
        or len(probe_class.recommended_detector) > 0
    )


@pytest.mark.parametrize("classname", probes)
def test_probe_detector_exists(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    probe_detectors = probe_class.recommended_detector + probe_class.extended_detectors
    if probe_class.primary_detector is not None:
        probe_detectors += [probe_class.primary_detector]
    assert set(probe_detectors).issubset(detector_bare_names)
