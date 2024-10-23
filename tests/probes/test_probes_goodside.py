import pytest
from garak import _config, _plugins
from garak.probes.goodside import WhoIsRiley, ThreatenJSON, Davidjl, Tag
from garak.translator import is_english
from garak.attempt import Attempt
import ast
import garak
import importlib

PROBES = [classname for (classname, active) in 
    _plugins.enumerate_plugins("probes") if "goodside" in classname]


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_Tag_attempt_descrs_translation():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe_tag = Tag(_config)

    convert_descr = []
    for descr in probe_tag.attempt_descrs:
        descr = ast.literal_eval(str(descr))
        convert_descr.append(descr)

    for i, descr in enumerate(convert_descr[:len(convert_descr)//2]):
        prompt_stub = descr["prompt_stub"]
        payload = descr["payload"]
        
        if isinstance(prompt_stub, list):
            prompt_stub = prompt_stub[0]
        if isinstance(payload, list):
            payload = payload[0]

        if is_english(prompt_stub):
            assert convert_descr[len(convert_descr)//2 + i]["prompt_stub"] != prompt_stub, "Prompt stub should be translated"
        if is_english(descr["payload"]):
            assert convert_descr[len(convert_descr)//2 + i]["payload"] != payload, "Payload should be translated"
    
    importlib.reload(garak._config)
    garak._config.load_base_config()


@pytest.mark.parametrize("classname", PROBES)
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_goodside_translation(classname):
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
    
    translated_prompts = probe_instance.translator.translate_prompts(probe_instance.prompts)
    assert isinstance(translated_prompts, list), "_translate should return a list"
    assert len(translated_prompts) > len(probe_instance.prompts), "_translate should add translated triggers"
    for index, prompt in enumerate(probe_instance.prompts):
        each_translated_prompt = translated_prompts[len(probe_instance.prompts) + index]
        if is_english(prompt) and is_english(each_translated_prompt) is False:
            assert each_translated_prompt != prompt

    importlib.reload(garak._config)
    garak._config.load_base_config()
