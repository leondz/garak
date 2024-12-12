import pytest
from garak.attempt import Attempt
from garak import _config
import garak
import importlib
from garak.detectors.snowball import DontStartNo, DontStartYes
from garak.harnesses.base import Harness
import os


@pytest.fixture
def dont_start_no_detector():
    local_config_path = str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    _config.run.translation["translation_service"] = 'local'
    _config.run.translation["lang_spec"] = "ja"
    _config.run.translation["model_spec"]["model_name"] = "facebook/m2m100_418M"
    _config.run.translation["model_spec"]["tokenizer_name"] = "facebook/m2m100_418M"
    detector = DontStartNo(_config)
    return detector


@pytest.fixture
def dont_start_yes_detector():
    local_config_path = str(_config.transient.package_dir / ".." / "tests" / "translator" / "test_config" / ("translation.yaml"))
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    _config.run.translation["translation_service"] = 'local'
    _config.run.translation["lang_spec"] = "ja"
    _config.run.translation["model_spec"]["model_name"] = "facebook/m2m100_418M"
    _config.run.translation["model_spec"]["tokenizer_name"] = "facebook/m2m100_418M"
    detector = DontStartYes(_config)
    return detector


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_dont_start_no_reverse_translation(dont_start_no_detector):
    attempt = Attempt(prompt="Does this start with no?")
    attempt.outputs = [
        "いいえ、それはしません。",  # "No, it doesn't." in Japanese
        "確かにそうです。",  # "Yes, it does." in Japanese
    ]

    results = dont_start_no_detector.detect(attempt)
    assert results == [1.0, 0.0], "Reverse translation results do not match expected values for DontStartNo"
    importlib.reload(garak._config)
    garak._config.load_base_config()


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_dont_start_yes_reverse_translation(dont_start_yes_detector):
    dont_detector = DontStartYes(_config) 
    attempt = Attempt(prompt="Does this start with yes?")
    attempt.outputs = [
        "はい、それはします。",  # "Yes, it does." in Japanese
        "いいえ、それはしません。",  # "No, it doesn't." in Japanese
    ]
    
    results = dont_start_yes_detector.detect(attempt)
    assert results == [1.0, 0.0], "Reverse translation results do not match expected values for DontStartYes"
    importlib.reload(garak._config)
    garak._config.load_base_config()
