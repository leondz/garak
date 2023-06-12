#!/usr/bin/env python3

import json

from garak.detectors.base import StringDetector


class SlursReclaimedSlurs(StringDetector):
    name = "slurs"
    description = "Slurs and reclaimed slurs"
    uri = "https://en.wikipedia.org/wiki/List_of_ethnic_slurs"
    bcp47 = "en"

    def __init__(self):
        self.substrings = set([])
        with open("resources/slurprompts.jsonl", "r") as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                self.substrings.add(json.loads(line)["term"])

        super().__init__(self.substrings)
        self.matchtype = "word"
