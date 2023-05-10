#!/usr/bin/env python3

class PersuaderProbe:
    def __init__(self):
        self.description = "Empty Persuader module"
        self.uri = ""
        self.bcp47 = None # language this is for, in bcp47 format
        self.recommended_detector = None
        pass
    
    def probe(self, target):
        # attempt to exploit the target, return list of results
        return []
