import pytest
import importlib
from garak import _config, _plugins
from garak.probes.continuation import ContinueSlursReclaimedSlurs, ContinueSlursReclaimedSlursMini
from garak.translator import is_english


@pytest.mark.parametrize("probe_class", [ContinueSlursReclaimedSlurs])
def test_probe_translation(probe_class):
    _config.run.translation_service = 'local'
    _config.run.lang_spec = 'jap'
    _config.run.seed = 42
    probe_instance = probe_class(config_root=_config)
    if hasattr(probe_instance, '_translate'):
        translated_prompts = probe_instance._translate(probe_instance.prompts)
        assert isinstance(translated_prompts, list)
        assert len(translated_prompts) > 0
        for index, prompt in enumerate(probe_instance.prompts):
            each_translated_prompt = translated_prompts[len(probe_instance.prompts) + index]
            if is_english(prompt) and is_english(each_translated_prompt) is False:
                assert each_translated_prompt != prompt, f"Prompt should be translated: {prompt}"