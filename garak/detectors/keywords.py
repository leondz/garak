from typing import List
from garak.detectors.base import TriggerListDetector
import garak.attempt 

class KeywordsFromTL(TriggerListDetector):
    """Detects keywords from the list of triggers"""

    doc_uri = "https://arxiv.org/pdf/2407.11969v2"
    bcp47 = "en"

    def detect(self, attempt: garak.attempt.Attempt) -> List[float]:
        detector_results = super().detect(attempt, case_sensitive=False)
        return detector_results