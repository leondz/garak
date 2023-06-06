#!/usr/bin/env python3

from garak.probes.base import TextProbe


class FalseAssertion50(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "falseassertion"
        self.description = "Does the model reject [questions based on] false claims?"
        self.bcp47 = "en"
        self.uri = "https://arxiv.org/abs/2304.13734"
        self.recommended_detector = [
            "misleading.MustRefuteClaimModel",
            "misleading.MustRefuteClaimKW",
            "mitigation.MitigationBypass",
            "misleading.MustContradictNLI",
        ]

        prefixes = ["", "Why is it that", "Explain why"]

        self.prompts = []

        for prefix in prefixes:
            for false_assertion in open("resources/truefalse_falseclaims_50.txt", "r"):
                false_assertion = false_assertion.strip()
                if not false_assertion:
                    continue
                if not prefix:
                    self.prompts.append(false_assertion)
                else:
                    if false_assertion.startswith("The"):
                        false_assertion = "t" + false_assertion[1:]
                    self.prompts.append(f"{prefix} {false_assertion}")
