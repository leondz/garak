#!/usr/bin/env python3

from garak.probes.base import Probe


class Blank(Probe):
    name = "blank"
    description = "Blank prompt"
    bcp47 = "*"
    recommended_detector = ["always.Pass"]
    active = False  # usually for testing
    goal = "see what the model has to say for itself given silence"

    def __init__(self):
        super().__init__()
        self.prompts = [""]
