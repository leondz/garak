import pytest
import os
from garak import _config, _plugins
import shutil
from garak.detectors.base import Detector, StringDetector, HFDetector
from garak.detectors.misleading import MustRefuteClaimModel, MustRefuteClaimKW, MustContradictNLI
from garak.detectors.leakreplay import StartsWith
from garak.probes.continuation import ContinueSlursReclaimedSlurs
from garak.probes.glitch import Glitch
from garak.probes.goodside import Tag
from garak.detectors.snowball import DontStartNo, DontStartYes

# force a local cache file to exist when this top level import is loaded
if not os.path.isfile(_plugins.PluginCache._user_plugin_cache_filename):
    _plugins.PluginCache.instance()


@pytest.fixture(autouse=True)
def config_report_cleanup(request):
    """Cleanup a testing and report directory once we are finished."""

    def remove_log_files():
        files = []
        if _config.transient.reportfile is not None:
            _config.transient.reportfile.close()
            report_html_file = _config.transient.report_filename.replace(
                ".jsonl", ".html"
            )
            hitlog_file = _config.transient.report_filename.replace(
                ".report.", ".hitlog."
            )
            files.append(_config.transient.report_filename)
            files.append(report_html_file)
            files.append(hitlog_file)

        for file in files:
            if os.path.exists(file):
                os.remove(file)

    request.addfinalizer(remove_log_files)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_storage(required_space_gb=1, path='/'): Skip the test if insufficient disk space."
    )


def check_storage(required_space_gb=1, path="/"):
    """
    Check the available disk space.

    Args:
        required_space_gb (float): Minimum required free space in GB.
        path (str): Filesystem path to check.

    Returns:
        bool: True if there is enough free space, False otherwise.
    """
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (2**30)  # Convert bytes to gigabytes

    return free_gb >= required_space_gb


def pytest_runtest_setup(item):
    """
    Called before each test is run. Performs a storage check if a specific marker is present.
    """
    marker = item.get_closest_marker("requires_storage")
    if marker:
        required_space_gb = marker.kwargs.get("required_space_gb", 1)  # Default is 1GB
        path = marker.kwargs.get("path", "/")  # Default is the root directory

        if not check_storage(required_space_gb, path):
            pytest.skip(f"❌ Skipping test. Not enough free space ({required_space_gb} GB) at '{path}'.")
        else:
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (2**30)  # Convert bytes to gigabytes
            print(f"✅ Sufficient free space ({free_gb:.2f} GB) confirmed.")


@pytest.fixture
def detector():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    detector = Detector(_config)
    return detector 


@pytest.fixture
def detector_start_with():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.bcp47 = "en"
    detector = StartsWith(_config)
    return detector 


@pytest.fixture
def detector_string_m2m100():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "ja"
    _config.plugins.generators["local_model_name"] = "facebook/m2m100_418M"
    _config.plugins.generators["local_tokenizer_name"] = "facebook/m2m100_418M"
    substrings = ["test", "example", "fabrication"]
    detector = StringDetector(substrings, _config)
    return detector 


@pytest.fixture
def detector_string():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    substrings = ["test", "example", "fabrication"]
    detector = StringDetector(substrings, _config)
    return detector 


@pytest.fixture
def hf_detector():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "ja"
    _config.plugins.generators["local_model_name"] = "facebook/m2m100_418M"
    _config.plugins.generators["local_tokenizer_name"] = "facebook/m2m100_418M"
    HFDetector.detector_model_path = "garak-llm/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli"
    HFDetector.detector_target_class = "label"
    HFDetector.tokenizer_kwargs = {"truncation": True, "max_length": 256}
    detector = HFDetector(_config)
    return detector 


@pytest.fixture
def claim_detector():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    detector = MustRefuteClaimKW(_config)
    return detector 


@pytest.fixture
def dont_start_no_detector():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "ja"
    _config.plugins.generators["local_model_name"] = "facebook/m2m100_418M"
    _config.plugins.generators["local_tokenizer_name"] = "facebook/m2m100_418M"
    detector = DontStartNo(_config)
    return detector


@pytest.fixture
def dont_start_yes_detector():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "ja"
    _config.plugins.generators["local_model_name"] = "facebook/m2m100_418M"
    _config.plugins.generators["local_tokenizer_name"] = "facebook/m2m100_418M"
    detector = DontStartYes(_config)
    return detector


@pytest.fixture
def probe_continue_slurs_reclaimed_slurs():
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = "jap"
    _config.plugins.generators["local_model_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.plugins.generators["local_tokenizer_name"] = "Helsinki-NLP/opus-mt-en-{}"
    _config.run.seed = 42
    probe = ContinueSlursReclaimedSlurs(_config)
    return probe 

