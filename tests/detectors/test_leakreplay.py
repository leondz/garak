import pytest
from garak.attempt import Attempt
from garak.detectors.leakreplay import StartsWith
from garak import _config


def test_startswith_detect():
    _config.run.translation_service = 'local'
    detector = StartsWith(_config)
    detector.bcp47 = "en"
    detector.target_lang = "jap"

    attempt = Attempt(prompt="This is a test prompt")
    attempt.notes["triggers"] = ["Hello", "Test"]
    attempt.outputs = [
        "Hello world",
        "This is a test",
        "Test case",
        "No match here"
    ]

    # Run the detection
    results = detector.detect(attempt)

    # Verify the results
    assert isinstance(results, list), "Detect method should return a list"
    assert len(results) == len(attempt.all_outputs), "Results should match the number of outputs"
    assert results == [1.0, 0.0, 1.0, 0.0], "Detection results do not match expected values"
