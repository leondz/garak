"""Always detectors

These always return a certain result, used mostly in testing
or to indicate where a class' child should override something."""

from typing import List

from garak.attempt import Attempt
from garak.detectors.base import Detector


class Fail(Detector):
    """Always Fail (for testing & prototyping)"""

    def detect(self, attempt: Attempt) -> List[float]:
        return [1.0] * len(attempt.outputs)


class Pass(Detector):
    """Always Pass (for testing & prototyping)"""

    def detect(self, attempt: Attempt) -> List[float]:
        return [0.0] * len(attempt.outputs)
