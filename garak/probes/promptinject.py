#!/usr/bin/env python3

from garak.attempt import Attempt
from garak.probes.base import Probe


class PromptInject(Probe):
    def __init__(self):
        super().__init__()
        self.name = "promptinject"
        self.description = "PromptInject is a framework that assembles prompts in a modular fashion to provide a quantitative analysis of the robustness of LLMs to adversarial prompt attacks. trophy Best Paper Awards @ NeurIPS ML Safety Workshop 2022"
        self.bcp47 = "en"
        self.uri = "https://openreview.net/forum?id=qiaRo_7Zmug"
        self.recommended_detector = [
            "promptinject.AttackRogueString",
        ]

        # procedure taken from https://github.com/agencyenterprise/PromptInject/blob/main/notebooks/Example.ipynb

        from resources.promptinject import (
            build_dataframe,
            build_prompts,
            get_metrics,
            prompt_data,
            run_prompts_api,
            score_attacks,
        )

        prompt_config = {
            "base": {
                "text": prompt_data.ALL_OPENAI_PLAYGROUND_PROMPTS,
            },
            "attack": {
                "text": (
                    prompt_data.goal_hikacking_attacks["ignore-print"],
                    prompt_data.goal_hikacking_attacks["ignore-say"],
                ),
                "rogue_string": prompt_data.rogue_strings["hate-humans"],
                "scoring": "match_rogue_to_output",
                "settings": {
                    "escape": prompt_data.escape_chars["n"],
                    "delimiter": prompt_data.delimiter_chars["dash"],
                    "escape_length": 10,
                    "escape_times": 2,
                },
            },
            "config": {
                "id": (0, 1, 2, 3),
            },
            "visualization": {"columns": ()},
        }
        # self.prompts.append(f"{prefix} {false_assertion}")

        self.prompts = []
        self.pi_prompts = build_prompts(prompt_config)
        for pi_prompt in self.pi_prompts:
            self.prompts.append(pi_prompt["prompt"])

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes["settings"] = self.pi_prompts[seq]["settings"]
        attempt.notes["trigger"] = self.pi_prompts[seq]["settings"][
            "attack_rogue_string"
        ]
        return attempt

    def _generator_precall_hook(self, generator, attempt):
        map_attribs = (
            "temperature top_p frequency_penalty presence_penalty max_tokens".split()
        )
        for map_attrib in map_attribs:
            if map_attrib in dir(generator):
                setattr(
                    generator,
                    map_attrib,
                    attempt.notes["settings"]["config_" + map_attrib],
                )
