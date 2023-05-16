#!/usr/bin/env python3

from probes.base import Probe

class RealToxicityPrompts(Probe):
    def __init__(self):
        super().__init__()
        self.description = "Implementation of probes in RealToxicityPrompts"
        self.lang = 'en'
        self.name = 'realtoxicityprompts'

