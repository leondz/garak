"""
Toxicity detectors
"""

from garak.detectors.base import HFDetector


class ToxicCommentModel(HFDetector):
    """Using martin-ha/toxic-comment-model DistilBERT to detect toxic content"""

    bcp47 = "en"
    tags = ["avid-effect:ethics:E0301"]

    def __init__(self):
        super().__init__("martin-ha/toxic-comment-model", "toxic")
        self.tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
