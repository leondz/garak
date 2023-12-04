#!/usr/bin/env python3
"""Snowball probe

Checks if the system gives wrong answers to complex reasoning questions,
instead of giving the right answer or no answer. Bsaed on

  https://arxiv.org/abs/2305.13534
"""

import json

from garak import _config
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
            _config.transient.basedir / "resources/graph_connectivity.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.prompts = json.load(f)


class GraphConnectivityMini(GraphConnectivity, Probe):
    __doc__ = GraphConnectivity.__doc__ + " - limited number of examples"
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
        with open(
            _config.transient.basedir / "resources/primality_testing.json",
            "r",
            encoding="utf-8",
        ) as f:
            dataset = json.load(f)
            self.prompts = [entry["question"] for entry in dataset]


class PrimesMini(Primes, Probe):
    __doc__ = Primes.__doc__ + " - limited number of examples"
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
        with open(
            _config.transient.basedir / "resources/senator_search.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.prompts = json.load(f)


class SenatorsMini(Senators, Probe):
    __doc__ = Senators.__doc__ + " - limited number of examples"
    active = True

    def __init__(self):
        super().__init__()
        self.prompts = self.prompts[-100:]
