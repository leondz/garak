import pytest
import random
from garak import _config
from garak.probes.glitch import Glitch, Glitch100
from garak.translator import is_english


def test_Glitch_translation():
    _config.run.translation_service = 'local'
    _config.run.lang_spec = 'jap'
    _config.run.seed = 42
    probe_instance = Glitch(config_root=_config)
    translated_triggers = probe_instance._translate(probe_instance.triggers)
    assert isinstance(translated_triggers, list), "_translate should return a list"
    assert len(translated_triggers) > len(probe_instance.triggers), "_translate should add translated triggers"
    for index, prompt in enumerate(probe_instance.triggers):
        each_translated_trigger = translated_triggers[len(probe_instance.triggers) + index]
        if is_english(prompt) and is_english(each_translated_trigger) is False:
            assert each_translated_trigger != prompt
