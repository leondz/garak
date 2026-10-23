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

BASE32 = EncodingStrategy(name="BASE32", encoders=(base64.b32encode,))
ASCII85 = EncodingStrategy(
    name="ASCII85", encoders=(base64.a85encode, base64.b85encode)
)
HEX = EncodingStrategy(name="hex", encoders=(binascii.b2a_hex,))


ROT13TRANS = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
)


def rot13(text: bytes) -> bytes:
    return bytes(text.decode().translate(ROT13TRANS), "utf-8")


def atbash(text: bytes) -> bytes:
    out = []
    for ch in text.decode():
        if "a" <= ch <= "z":
            out.append(chr(ord("z") - (ord(ch) - ord("a"))))
        elif "A" <= ch <= "Z":
            out.append(chr(ord("Z") - (ord(ch) - ord("A"))))
        else:
            out.append(ch)
    return "".join(out).encode("utf-8")


def uuencode(payload: bytes) -> str:
    chunks = []
    for i in range(0, len(payload), 45):
        chunks.append(binascii.b2a_uu(payload[i : i + 45]))
    return "".join(map(bytes.decode, chunks))


# Custom-function encoders: ROT13 and Atbash pass digits and punctuation through
# in clear; UU introduces line breaks in its output.
ROT13 = EncodingStrategy(name="ROT13", encoders=(rot13,))
ATBASH = EncodingStrategy(name="Atbash", encoders=(atbash,))
UU = EncodingStrategy(name="UUencode", encoders=(uuencode,))


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
