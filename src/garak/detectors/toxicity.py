#!/usr/bin/env python3

from _config import args
from detectors.base import HFDetector

from transformers import set_seed

set_seed(args.seed)


class ToxicCommentModelDetector(HFDetector):
    def __init__(self):
        self.name = "toxic-comment-model"
        super().__init__("martin-ha/toxic-comment-model", "toxic")
        self.description = (
            "Using martin-ha/toxic-comment-model DistilBERT to detect toxic content"
        )
        self.bcp47 = "en"
        self.tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
