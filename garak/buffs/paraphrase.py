#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Buff that paraphrases a prompt. """

from collections.abc import Iterable

import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

import garak.attempt
from garak.buffs.base import Buff


class PegasusParaphrase(Buff):
    """Paraphrasing buff using Pegasus model"""

    bcp47 = "en"

    def __init__(self) -> None:
        super().__init__()
        self.para_model_name = "tuner007/pegasus_paraphrase"  # https://huggingface.co/tuner007/pegasus_paraphrase
        self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 60
        self.temperature = 1.5
        self.num_return_sequences = 6
        self.num_beams = self.num_return_sequences

    def _load(self) -> None:
        self.tokenizer = PegasusTokenizer.from_pretrained(self.para_model_name)
        self.para_model = PegasusForConditionalGeneration.from_pretrained(
            self.para_model_name
        ).to(self.torch_device)

    def get_response(self, input_text):
        if "para_model" not in dir(self):
            self._load()
        batch = self.tokenizer(
            [input_text],
            truncation=True,
            padding="longest",
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.torch_device)
        translated = self.para_model.generate(
            **batch,
            max_length=self.max_length,
            num_beams=self.num_beams,
            num_return_sequences=self.num_return_sequences,
            temperature=self.temperature,
        )
        tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        paraphrases = self.get_response(attempt.prompt)
        for paraphrase in set(paraphrases):
            attempt.prompt = paraphrase
            yield attempt
