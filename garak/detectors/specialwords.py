#!/usr/bin/env python3

import json

from garak.detectors.base import StringDetector


class SlursReclaimedSlurs(StringDetector):
    def __init__(self):
        self.name = "slurs"
        self.substrings = set([])
        with open("resources/slurprompts.jsonl", "r") as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                self.substrings.add(json.loads(line)["term"])

        super().__init__(self.substrings)
        self.description = "Slurs and reclaimed slurs"
        self.matchtype = "word"
