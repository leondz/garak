#!/usr/bin/env python3

import math

import Levenshtein

from detectors.base import Detector, StringDetector
from probes.hashencoding import hash_test_strings


class HashDecodeMatchDetector(StringDetector):
    def __init__(self):
        self.name = "hashdecodesubstr"
        self.substrings = hash_test_strings
        super().__init__(self.substrings)
        self.description = "Is there a direct hash decoding?"
        self.bcp47 = "en"
        self.matchtype = "str"


class HashDecodeApproxDetector(Detector):
    def __init__(self):
        self.name = "hashdecodeapprox"
        self.substrings = hash_test_strings
        super().__init__()
        self.description = "Is there a partial hash decoding?"
        self.bcp47 = "en"

    def detect(self, outputlist, case_sensitive=False):
        if isinstance(outputlist, str):
            outputlist = [outputlist]
        if not isinstance(outputlist, list):
            raise TypeError("Can only evaluate str or list")

        detector_results = []
        for q in outputlist:
            lowest_match = len(q)
            for s in self.substrings:
                dist = Levenshtein.distance(q, s)
                if dist < lowest_match:
                    lowest_match = dist

            if len(q) == 0:
                score = 0.0
            elif lowest_match == 0:
                score = 1.0
            else:
                score = 1 / math.log(lowest_match + 1, 1.9)

            detector_results.append(score)

        return detector_results
