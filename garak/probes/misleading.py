#!/usr/bin/env python3

import garak._config
from garak.probes.base import TextProbe


class FalseAssertion50(TextProbe):
    name = "falseassertion"
    description = "Does the model reject [questions based on] false claims?"
    bcp47 = "en"
    uri = "https://arxiv.org/abs/2304.13734"
    recommended_detector = [
        "misleading.MustRefuteClaimModel",
        "misleading.MustRefuteClaimKW",
        "mitigation.MitigationBypass",
        "misleading.MustContradictNLI",
    ]

    def __init__(self):
        super().__init__()

        prefixes = ["", "Why is it that", "Explain why"]

        self.prompts = []

        for prefix in prefixes:
            for false_assertion in open(garak._config.basedir / "resources/truefalse_falseclaims_50.txt", "r"):
                false_assertion = false_assertion.strip()
                if not false_assertion:
                    continue
                if not prefix:
                    self.prompts.append(false_assertion)
                else:
                    if false_assertion.startswith("The"):
                        false_assertion = "t" + false_assertion[1:]
                    self.prompts.append(f"{prefix} {false_assertion}")
