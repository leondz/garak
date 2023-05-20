#!/usr/bin/env python3

from collections import defaultdict
import json

from probes.base import TextProbe


class ContinueSlursReclaimedSlurs(TextProbe):
    def __init__(self):
        super().__init__()
        self.name = "continueslur"
        self.description = "Continue partial word with slur or reclaimed slur"
        self.bcp47 = "en"
        self.uri = ""
        self.recommended_detector = [
            "specialwords.SlursReclaimedSlurs",
        ]
        # go through the list
        # for each term, work out first char, first three chars, all but last two chars
        # append these to each of the prefixes for that term
        slur_prefixes = defaultdict(set)
        with open('detectors/slurprompts.jsonl', 'r') as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                slur_prefixes[entry['term']].add(entry['prefix'])

        self.prompts = set()
        for term in slur_prefixes.keys():
            term_variants = set([term[0], term[:3], term[:-2]])
            for prefix in slur_prefixes[term]:
                for term_variant in term_variants:
                    self.prompts.add(prefix +  term_variant)
