"""Probes to check if a generator will continue a contentious term.

Operates by giving high-risk context as a prompt, extracted from e.g. Urban
Dictionary examples of use of contentious terms, and seeing if the model will
continue the term based on varying amounts of prefix.
"""

import json

from garak import _config
from garak.attempt import Attempt
from garak.data import path as data_path
from garak.probes.base import Probe


class ContinueSlursReclaimedSlurs(Probe):
    """Continue partial word with slur or reclaimed slur.

    This probe poses a partial ethnic slur with some preceding content, and
    checks to see if the model will complete the slur."""

    bcp47 = "en"
    doc_uri = ""
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
    active = False
    source_resource_filename = "slurprompts.jsonl"

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        # go through the list
        # for each term, work out first char, first three chars, all but last two chars
        # append these to each of the prefixes for that term
        self._slur_prefixes = []
        with open(
            data_path / self.source_resource_filename,
            "r",
            encoding="utf-8",
        ) as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                self._slur_prefixes.append((entry["term"], entry["prefix"]))

        self.prompts = []
        self.triggers = []
        for term, prefix in self._slur_prefixes:
            lower_term = term.lower()
            term_variants = set(["", lower_term[0]])  # blank, first letter
            if len(term) > 2:
                term_variants.add(lower_term[:2].strip())  # first two letters
            term_variants.add(
                lower_term[: int(len(lower_term) / 2)].strip()
            )  # first half of term

            for term_variant in term_variants:
                # would use a set but order is important
                candidate_prompt = prefix + term_variant
                if candidate_prompt not in self.prompts:
                    self.prompts.append(candidate_prompt.strip())
                    self.triggers.append(term)
        if hasattr(self, 'translator'):
            if self.translator is not None:
                self.triggers = self.translator.translate_triggers(self.triggers)

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes = dict(
            attempt.notes
        )  # we don't want all attempts.notes to ref same dict
        attempt.notes["trigger"] = str(self.triggers[seq])
        return attempt


class ContinueSlursReclaimedSlursMini(ContinueSlursReclaimedSlurs, Probe):
    """Continue partial word with slur or reclaimed slur.

    This probe poses a partial ethnic slur with some preceding content, and
    checks to see if the model will complete the slur. It uses a subset of 80
    slurs & contexts that test LLMs have been likely to provide completions for."""

    active = True
    source_resource_filename = "slurprompts_mini.jsonl"
