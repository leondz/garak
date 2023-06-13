#!/usr/bin/env python3
# probe for confident, incorrect answers to complex reasoning/retrieval questions

import json

import garak._config
from garak.probes.base import TextProbe


class GraphConnectivity(TextProbe):
    name = "connectingflights"
    description = "Probe asking for impossible flight routings"
    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartYes"]

    def __init__(self):
        super().__init__()
        with open(garak._config.basedir / "resources/graph_connectivity.json", "r") as f:
            self.prompts = json.load(f)


class Primes(TextProbe):
    name = "primes"
    description = "Ask model to check a list of higher primes"
    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartNo"]

    def __init__(self):
        super().__init__()
        with open(garak._config.basedir / "resources/primality_testing.json", "r") as f:
            dataset = json.load(f)
            self.prompts = [entry["question"] for entry in dataset]


class Senators(TextProbe):
    name = "senators"
    description = "Asking for senators that don't exist"
    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartYes"]

    def __init__(self):
        super().__init__()
        with open(garak._config.basedir / "resources/senator_search.json", "r") as f:
            self.prompts = json.load(f)
