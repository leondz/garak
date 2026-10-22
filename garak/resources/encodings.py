# SPDX-FileCopyrightText: Portions Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Encoding functions

Functions used to offer various encodings that are needed more than one place in garak
"""

import base64
import binascii
import random
from dataclasses import dataclass
from typing import Callable, List, Tuple


@dataclass(frozen=True)
class EncodingStrategy:
    """A named encoding technique: ordered encoder callables, applied in order.

    Pure data: ``encode`` returns one output per encoder (duplicates kept).
    """

    name: str
    encoders: Tuple[Callable, ...]
    use_bytes: bool = True

    def encode(self, text: str) -> List[str]:
        """Return one encoded string per encoder, in declaration order."""
        encoded_texts: List[str] = []
        for encoder in self.encoders:
            if self.use_bytes:
                encoded_text = encoder(bytes(text, "utf-8"))
            else:
                encoded_text = encoder(text)
            if isinstance(encoded_text, bytes):
                encoded_text = encoded_text.decode()
            encoded_texts.append(encoded_text)
        return encoded_texts


# Shared strategies consumed by both the decode-and-repeat probes and the
# additive decode-and-act IntentProbe siblings. The encoder tuples and names are
# the exact values the ``InjectBase16`` / ``InjectBase64`` classes used, so
# delegation is behaviour-neutral.
BASE16 = EncodingStrategy(name="BASE16", encoders=(base64.b16encode,))
BASE64 = EncodingStrategy(
    name="BASE64",
    encoders=(
        base64.b64encode,
        base64.urlsafe_b64encode,
        base64.standard_b64encode,
        binascii.b2a_base64,
    ),
)


def leetspeak(input: str, transmute_chance: float = 0.6) -> str:
    src_chars = "ieaost"
    dst_chars = "134057"
    processed = input.translate(
        str.maketrans(src_chars.lower() + src_chars.upper(), dst_chars + dst_chars)
    )
    # mix it up
    output = "".join(
        [processed[i] if random.random() > 0.5 else input[i] for i in range(len(input))]
    )
    return output
