#!/usr/bin/env python3

from garak.probes.base import Probe


class RealToxicityPrompts(Probe):
    def __init__(self):
        super().__init__()
        self.description = "Implementation of probes in RealToxicityPrompts"
        self.bcp47 = "en"
        self.name = "realtoxicityprompts"
        self.prompts = []
        self.recommended_detector = []
