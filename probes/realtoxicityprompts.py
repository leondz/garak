#!/usr/bin/env python3

from persuader.persuadermodule import PersuaderModule

class RealToxicityPrompts(PersuaderModule):
    def __init__(self):
        super().__init__()
        self.description = "Implementation of RealToxicityPrompts"
        self.lang = 'en'

