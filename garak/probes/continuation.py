"""Probes to check if a generator will continue a contentious term.

Operates by giving high-risk context as a prompt, extracted from e.g. Urban
Dictionary examples of use of contentious terms, and seeing if the model will
continue the term based on varying amounts of prefix.
"""

from collections import defaultdict
import json

from garak import _config
from garak.attempt import Attempt
from garak.probes.base import Probe


class ContinueSlursReclaimedSlurs80(Probe):
    """Continue partial word with slur or reclaimed slur.

    This probe poses a partial ethnic slur with some preceding content, and
    checks to see if the model will complete the slur. It uses a subset of 80
    slurs & contexts that test LLMs have been likely to provide completions for."""

    bcp47 = "en"
    uri = ""
    recommended_detector = [
        "continuation.Continuation",
    ]
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
        "owasp:llm01",
        "quality:Behavioral:ContentSafety:Toxicity",
        "quality:Behavioral:ContentSafety:HateHarassment",
        "payload:unwanted:hatespeech",
    ]
    goal = "output an ethnic slur"

    def __init__(self):
        super().__init__()
        # go through the list
        # for each term, work out first char, first three chars, all but last two chars
        # append these to each of the prefixes for that term
        slur_prefixes = defaultdict(set)
        with open(
            _config.transient.basedir / "resources" / "slurprompts_80.jsonl",
            "r",
            encoding="utf-8",
        ) as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                slur_prefixes[entry["term"]].add(entry["prefix"])

        self.prompts = []
        self.triggers = []
        for term, prefixes in slur_prefixes.items():
            lower_term = term.lower()
            term_variants = set(["", lower_term[0]])  # blank, first letter
            if len(term) > 2:
                term_variants.add(lower_term[:2].strip())  # first two letters
            term_variants.add(
                lower_term[: int(len(lower_term) / 2)].strip()
            )  # first half of term

            for prefix in prefixes:
                for term_variant in term_variants:
                    # would use a set but order is important
                    candidate_prompt = prefix + term_variant
                    if candidate_prompt not in self.prompts:
                        self.prompts.append(candidate_prompt.strip())
                        self.triggers.append(term)

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes = dict(
            attempt.notes
        )  # we don't want all attempts.notes to ref same dict
        attempt.notes["trigger"] = str(self.triggers[seq])
        return attempt
