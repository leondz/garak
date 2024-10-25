import pytest
import random
from garak import _config, _plugins
from garak.translator import is_english
import garak
import importlib

PROBES = [classname for (classname, active) in 
    _plugins.enumerate_plugins("probes") if "glitch" in classname]

@pytest.mark.parametrize("classname", PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_Glitch_translation(classname):
    plugin_name_parts = classname.split(".")
    module_name = "garak." + ".".join(plugin_name_parts[:-1])
    class_name = plugin_name_parts[-1]
    mod = importlib.import_module(module_name)
    probe_class = getattr(mod, class_name)
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe_instance = probe_class(config_root=_config)
    translated_triggers = probe_instance.translator.translate_prompts(probe_instance.triggers)
    assert isinstance(translated_triggers, list), "_translate should return a list"
    assert len(translated_triggers) > len(probe_instance.triggers), "_translate should add translated triggers"
    for index, prompt in enumerate(probe_instance.triggers):
        each_translated_trigger = translated_triggers[len(probe_instance.triggers) + index]
        if is_english(prompt) and is_english(each_translated_trigger) is False:
            assert each_translated_trigger != prompt

    importlib.reload(garak._config)
    garak._config.load_base_config()