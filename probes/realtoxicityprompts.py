#!/usr/bin/env python3

from base import PersuaderProbe

class RealToxicityPrompts(PersuaderProbe):
    def __init__(self):
        super().__init__()
        self.description = "Implementation of probes in RealToxicityPrompts"
        self.lang = 'en'

