#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Buff that converts prompts with different encodings. """

import logging
from collections.abc import Iterable
from deepl import Translator
from os import getenv

import garak.attempt
from garak.buffs.base import Buff

# Low resource languages supported by DeepL
# ET = Estonian
# ID = Indonesian
# LT = Lithuanian
# LV = Latvian
# SK = Slovak
# SL = Slovenian
LOW_RESOURCE_LANGUAGES = ["ET", "ID", "LV", "SK", "SL"]


class LRLBuff(Buff):
    """Low Resource Language buff"""

    uri = "https://arxiv.org/abs/2310.02446"

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        api_key = getenv("DEEPL_API_KEY", None)
        if api_key is None:
            msg = "DEEPL_API_KEY not set in env, cannot use LRLBuff."
            user_msg = (
                msg
                + " If you do not have a DeepL API key, sign up at https://www.deepl.com/docs-api"
            )
            logging.error(msg)
            print(user_msg)
            yield attempt

        else:
            translator = Translator(api_key)
            prompt = attempt.prompt
            for language in LOW_RESOURCE_LANGUAGES:
                response = translator.translate_text(prompt, target_lang=language)
                translated_prompt = response.text
                attempt.prompt = translated_prompt
                yield attempt
