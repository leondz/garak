#!/usr/bin/env python3

from modules.persuadermodule import PersuaderModule, PersuaderHFDetector

class RealToxicityPrompts(PersuaderModule):
    def __init__(self):
        super().__init__()
        self.description = "Implementation of RealToxicityPrompts"
        self.lang = 'en'

class ToxicCommentModelDetector(PersuaderHFDetector):
    def __init__(self):
        super().__init__("martin-ha/toxic-comment-model", "toxic")
        self.description = "Using martin-ha/toxic-comment-model DistilBERT to detect toxic content"
        self.lang = 'en'
