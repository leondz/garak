#!/usr/bin/env python3
"""Test Probes

Probes that help with testing, but aren't necessarily useful in
deployment practice."""


from garak.probes.base import Probe


class Blank(Probe):
    """Blank prompt

    Poses a blank prompt to the model"""

    bcp47 = "*"
    active = False  # usually for testing
    goal = "see what the model has to say for itself given silence"
    uri = ""
    tags = []

    recommended_detector = ["always.Pass"]
    prompts = [""]
