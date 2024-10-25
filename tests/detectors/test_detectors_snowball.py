import pytest
from garak.attempt import Attempt
from garak import _config
import garak
import importlib


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_dont_start_no_reverse_translation(dont_start_no_detector):
    attempt = Attempt(prompt="Does this start with no?")
    attempt.outputs = [
        "いいえ、それはしません。",  # "No, it doesn't." in Japanese
        "確かにそうです。",  # "Yes, it does." in Japanese
    ]

    results = dont_start_no_detector.detect(attempt)
    assert results == [1.0, 0.0], "Reverse translation results do not match expected values for DontStartNo"


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_dont_start_yes_reverse_translation(dont_start_yes_detector):
    attempt = Attempt(prompt="Does this start with yes?")
    attempt.outputs = [
        "はい、それはします。",  # "Yes, it does." in Japanese
        "いいえ、それはしません。",  # "No, it doesn't." in Japanese
    ]

    results = dont_start_yes_detector.detect(attempt)
    assert results == [1.0, 0.0], "Reverse translation results do not match expected values for DontStartYes"
