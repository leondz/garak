import pytest
import os
import tempfile

from garak._plugins import PluginCache


@pytest.fixture(autouse=True)
def reset_cache(request) -> None:
    def reset_plugin_cache():
        PluginCache._plugin_cache_dict = None

    request.addfinalizer(reset_plugin_cache)


@pytest.fixture
def temp_cache_location(request) -> None:
    # override the cache file with a tmp location
    with tempfile.NamedTemporaryFile(buffering=0, delete=False) as tmp:
        PluginCache._user_plugin_cache_file = tmp.name
        PluginCache._plugin_cache_file = tmp.name
        tmp.close()
        os.remove(tmp.name)
    # reset the class level singleton
    PluginCache._plugin_cache_dict = None

    def remove_cache_file():
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    request.addfinalizer(remove_cache_file)

    return tmp.name


def test_create(temp_cache_location):
    cache = PluginCache.instance()
    assert os.path.isfile(temp_cache_location)
    assert isinstance(cache, dict)


def test_existing():
    info = PluginCache.plugin_info("probes.test.Test")
    assert isinstance(info, dict)


def test_missing_from_cache():
    cache = PluginCache.instance()["probes"]
    del cache["probes.test.Test"]
    assert cache.get("probes.test.Test") is None
    info = PluginCache.plugin_info("probes.test.Test")
    assert isinstance(info, dict)


def test_unknown_type():
    with pytest.raises(ValueError) as exc_info:
        info = PluginCache.plugin_info("fake.test.missing")
    assert "plugin type" in str(exc_info.value)


def test_unknown_class():
    with pytest.raises(ValueError) as exc_info:
        info = PluginCache.plugin_info("probes.test.missing")
    assert "plugin from " in str(exc_info.value)


def test_unknown_module():
    with pytest.raises(ValueError) as exc_info:
        info = PluginCache.plugin_info("probes.invalid.missing")
    assert "plugin module" in str(exc_info.value)


def test_unknown_module():
    with pytest.raises(ValueError) as exc_info:
        info = PluginCache.plugin_info("probes.invalid.format.length")
    assert "plugin class" in str(exc_info.value)
