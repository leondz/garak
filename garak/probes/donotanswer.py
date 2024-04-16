#!/usr/bin/env python3
"""
Do-Not-Answer Probes

https://github.com/Libr-AI/do-not-answer
https://arxiv.org/abs/2308.13387

An open-source dataset to evaluate LLMs' safety mechanism at a low cost.
The dataset consists only of prompts to which responsible language models should not answer.
"""

import sys

from garak import _config
from garak.probes.base import Probe

this = sys.modules[__name__]

def load_local_data(self):
    pass

def local_constructor(self):
    super(self.__class__, self).__init__()
    self.load_data()

class DoNotAnswer_Probe(Probe):
    """Do Not Answer probe

    A curated list of questions provided in the scientific research
    which are to be supplied as prompts and LLMs should not respond back."""

    probe_tags = [
        "discrimination_exclusion_toxicity_hateful_offensive",
        "human_chatbox",
        "information_hazard",
        "malicious_uses",
        "misinformation_harms",
    ]
    goal = "Check if the model answers to unwanted prompts"
    
    prompts = ["<|endoftext|>", ".", "<Links>", "<Wiki>", ""]

    '''for tag in probe_tags:
        # load filter lists
        with open(
            _config.transient.basedir
            / f"resources/donotanswer/{tag}.txt",
            encoding="utf=8",
        ) as f:
            prompts.append(f.read().strip().split("\n"))'''


    max_challenging = {}

    for tag in probe_tags:
        # load filter lists
        with open(
            _config.transient.basedir
            / f"resources/donotanswer/{tag}.txt",
            encoding="utf=8",
        ) as f:
            max_challenging[tag] = f.read().strip().split("\n")

        # define class
        classname = "DoNotAnswer_" + tag.title()
        descr = f"Implementation of {tag} probes in DoNotAnswer_Prompts"
        bcp47 = "en"

        setattr(
            this,
            classname,
            type(
                classname, 
                (Probe,),
                {
                    "__init__": local_constructor,
                    "uri": "https://arxiv.org/abs/2308.13387",
                    "bcp47": bcp47,
                    "description": descr,
                    "primary_detector": "mitigation.MitigationBypass",
                    "prompts": max_challenging[tag],
                    "load_data": load_local_data,
                    "goal": "generate " + tag.replace("_", " ") + " content",
                },
            ),
        )