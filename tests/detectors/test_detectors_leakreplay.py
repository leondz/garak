import pytest
from garak.attempt import Attempt
from garak import _config
import garak
import importlib


@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_startswith_detect(detector_start_with):
    detector = detector_start_with

    attempt = Attempt(prompt="This is a test prompt")
    attempt.notes["triggers"] = ["Hello", "Test"]
    attempt.outputs = [
        "Hello world",
        "This is a test",
        "Test case",
        "No match here",
        "陰府 の 端 に は 陰府 の 穴 が あ る."
    ]

    # Run the detection
    results = detector.detect(attempt)

    # Verify the results
    assert isinstance(results, list), "Detect method should return a list"
    assert len(results) == len(attempt.all_outputs), "Results should match the number of outputs"
    assert results == [1.0, 0.0, 1.0, 0.0, 1.0], "Detection results do not match expected values"
