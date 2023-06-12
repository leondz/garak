#!/usr/bin/env python3

from collections import defaultdict
import json

from garak.attempt import Attempt
from garak.probes.base import TextProbe


class ContinueSlursReclaimedSlurs50(TextProbe):
    name = "continueslur"
    description = "Continue partial word with slur or reclaimed slur"
    bcp47 = "en"
    uri = ""
    recommended_detector = [
        "specialwords.SlursReclaimedSlurs",
        "continuation.Continuation",
    ]

    def __init__(self):
        super().__init__()
        # go through the list
        # for each term, work out first char, first three chars, all but last two chars
        # append these to each of the prefixes for that term
        slur_prefixes = defaultdict(set)
        with open("resources/slurprompts_80.jsonl", "r") as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                slur_prefixes[entry["term"]].add(entry["prefix"])

        self.prompts = []
        self.triggers = []
        for term in slur_prefixes.keys():
            lower_term = term.lower()
            term_variants = set(["", lower_term[0]])  # blank, first letter
            if len(term) > 2:
                term_variants.add(lower_term[:2].strip())  # first two letters
            term_variants.add(
                lower_term[: int(len(lower_term) / 2)].strip()
            )  # first half of term

            for prefix in slur_prefixes[term]:
                for term_variant in term_variants:
                    # would use a set but order is important
                    candidate_prompt = prefix + term_variant
                    if candidate_prompt not in self.prompts:
                        self.prompts.append(candidate_prompt.strip())
                        self.triggers.append(term)

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes["trigger"] = self.triggers[seq]
        return attempt
