#!/usr/bin/env python3

import json

from garak.probes.base import Probe, TextProbe


class GraphConnectivity(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "connectingflights"
        self.description = "Probe asking for impossible flight routings"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.StartsNo"]
        with open("resources/graph_connectivity.json", "r") as f:
            self.prompts = json.load(f)


class Primes(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "primes"
        self.description = "List of higher primes"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.StartsYes"]
        with open("resources/primality_testing.json", "r") as f:
            self.prompts = json.load(f)


class Senators(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "senators"
        self.description = "Asking for senators that don't exist"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.StartsNo"]
        with open("resources/senator_search.json", "r") as f:
            self.prompts = json.load(f)
