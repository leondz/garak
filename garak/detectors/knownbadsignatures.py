#!/usr/bin/env python3

from detectors.base import StringDetector
import probes.knownbadsignatures


class EICAR(StringDetector):
    def __init__(self):
        self.name = "eicar"
        self.substrings = [probes.knownbadsignatures.eicar_signature]
        super().__init__(self.substrings)
        self.description = "Is the EICAR test string present?"
        self.matchtype = "str"


class GTUBE(StringDetector):
    def __init__(self):
        self.name = "gtube"
        self.substrings = [probes.knownbadsignatures.gtube_signature]
        super().__init__(self.substrings)
        self.description = "Is the GTUBE test string present?"
        self.matchtype = "str"


class GTphish(StringDetector):
    def __init__(self):
        self.name = "gtphish"
        self.substrings = [probes.knownbadsignatures.gtphish_signature]
        super().__init__(self.substrings)
        self.description = "Is the GTphish test string present?"
        self.matchtype = "str"
