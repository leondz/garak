#!/usr/bin/env python3
"""Snowball probe

Checks if the system gives wrong answers to complex reasoning questions,
instead of giving the right answer or no answer. Bsaed on

  https://arxiv.org/abs/2305.13534
"""

import json

import garak._config
from garak.probes.base import Probe


class GraphConnectivity(Probe):
    """Probe asking for impossible flight routings"""

    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartYes"]
    tags = ["avid:performance:P0204"]
    goal = "trick the model into saying an impossible flight routing is possible"
    active = False

    def __init__(self):
        super().__init__()
        with open(
            garak._config.basedir / "resources/graph_connectivity.json", "r"
        ) as f:
            self.prompts = json.load(f)


class GraphConnectivityMini(GraphConnectivity, Probe):
    active = True

    def __init__(self):
        super().__init__()
        self.prompts = self.prompts[-100:]


class Primes(Probe):
    """Ask model to check a list of higher primes"""

    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartNo"]
    tags = ["avid:performance:P0204"]
    goal = "trick the model into saying a prime model isn't prime"
    active = False

    def __init__(self):
        super().__init__()
        with open(garak._config.basedir / "resources/primality_testing.json", "r") as f:
            dataset = json.load(f)
            self.prompts = [entry["question"] for entry in dataset]


class PrimesMini(Primes, Probe):
    active = True

    def __init__(self):
        super().__init__()
        self.prompts = self.prompts[-100:]


class Senators(Probe):
    """Asking for senators that don't exist"""

    bcp47 = "en"
    uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    recommended_detector = ["snowball.DontStartYes"]
    tags = ["avid:performance:P0204"]
    goal = "trick the model into saying a fictitious senator exists"
    active = False

    def __init__(self):
        super().__init__()
        with open(garak._config.basedir / "resources/senator_search.json", "r") as f:
            self.prompts = json.load(f)


class SenatorsMini(Senators, Probe):
    active = True

    def __init__(self):
        super().__init__()
        self.prompts = self.prompts[-100:]
