#!/usr/bin/env python3
# probe for confident, incorrect answers to complex reasoning/retrieval questions

import json

from garak.probes.base import TextProbe


class GraphConnectivity(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "connectingflights"
        self.description = "Probe asking for impossible flight routings"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.DontStartYes"]
        with open("resources/graph_connectivity.json", "r") as f:
            self.prompts = json.load(f)


class Primes(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "primes"
        self.description = "List of higher primes"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.DontStartNo"]
        with open("resources/primality_testing.json", "r") as f:
            dataset = json.load(f)
            self.prompts = [entry["question"] for entry in dataset]


class Senators(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "senators"
        self.description = "Asking for senators that don't exist"
        self.bcp47 = "en"
        self.uri = "https://github.com/Nanami18/Snowballed_Hallucination"
        self.recommended_detector = ["snowball.DontStartYes"]
        with open("resources/senator_search.json", "r") as f:
            self.prompts = json.load(f)
