import pytest
from garak import _config, _plugins
from garak.probes.goodside import Tag
from garak.translator import is_english, convert_json_string
from garak.attempt import Attempt
import ast
import garak
import importlib
import json
from garak.harnesses.base import Harness
import os


PROBES = [classname for (classname, active) in 
    _plugins.enumerate_plugins("probes") if "goodside" in classname]


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_Tag_attempt_descrs_translation():
    local_config_path = str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation_local_low.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    _config.run.translation["translation_service"] = 'local'
    _config.run.translation["lang_spec"] = "jap"
    _config.run.translation["model_spec"]["model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.translation["model_spec"]["tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe_tag = Tag(_config)

    translated_attempt_descrs = probe_tag.attempt_descrs
    half_length = len(translated_attempt_descrs) // 2

    for i in range(half_length):

        convert_translated_attempt_descrs = json.loads(convert_json_string(translated_attempt_descrs[half_length + i]))
        convert_descr = json.loads(convert_json_string(translated_attempt_descrs[i]))
        if convert_descr["prompt_stub"] != "": 
            assert convert_descr["prompt_stub"] != convert_translated_attempt_descrs["prompt_stub"], "Prompt stub should be translated"
        if convert_descr["payload"] != "": 
            assert convert_descr["payload"] != convert_translated_attempt_descrs["payload"], "Payload should be translated"
    
    importlib.reload(garak._config)
    garak._config.load_base_config()

