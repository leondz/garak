import pytest
from garak import _config
from garak.probes.goodside import WhoIsRiley, ThreatenJSON, Davidjl, Tag
from garak.translator import is_english
from garak.attempt import Attempt
import ast


@pytest.fixture(scope="function")
def test_Tag_attempt_descrs_translation(tag_instance):
    _config.run.translation_service = 'local'
    _config.run.lang_spec = 'jap'
    _config.run.seed = 42
    probe_instance = Tag(config_root=_config)
    convert_descr = []
    for descr in probe_instance.attempt_descrs:
        descr = ast.literal_eval(str(descr))
        convert_descr.append(descr)
    
    for i, descr in enumerate(convert_descr[:len(convert_descr)//2]):
        if is_english(descr["prompt_stub"]):
            assert convert_descr[len(convert_descr)//2 + i]["prompt_stub"] != descr["prompt_stub"], "Prompt stub should be translated"
        if is_english(descr["payload"]):
            assert convert_descr[len(convert_descr)//2 + i]["payload"] != descr["payload"], "Payload should be translated"
    