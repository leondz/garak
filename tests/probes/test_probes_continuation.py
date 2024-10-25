import pytest
import importlib
from garak import _config, _plugins
from garak.probes.continuation import ContinueSlursReclaimedSlurs
from garak.translator import is_english
import garak
import importlib


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_probe_translation(probe_continue_slurs_reclaimed_slurs):
    probe_instance = probe_continue_slurs_reclaimed_slurs 
    if hasattr(probe_instance, 'translator'):
        translated_prompts = probe_instance.translator.translate_prompts(probe_instance.prompts)
        assert isinstance(translated_prompts, list)
        assert len(translated_prompts) > 0
        for index, prompt in enumerate(probe_instance.prompts):
            each_translated_prompt = translated_prompts[len(probe_instance.prompts) + index]
            if is_english(prompt) and is_english(each_translated_prompt) is False:
                assert each_translated_prompt != prompt, f"Prompt should be translated: {prompt}"
