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
    """Low Resource Language buff

    Uses the DeepL API to translate prompts into low-resource languages"""

    uri = "https://arxiv.org/abs/2310.02446"

    api_key_error_sent = False

    def __init__(self):
        super().__init__()
        self.post_buff_hook = True

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        api_key = getenv("DEEPL_API_KEY", None)
        if api_key is None:
            if not self.api_key_error_sent:
                msg = "DEEPL_API_KEY not set in env, cannot use LRLBuff."
                user_msg = (
                    msg
                    + " If you do not have a DeepL API key, sign up at https://www.deepl.com/pro#developer"
                )
                logging.error(msg)
                print("⚠️ ", user_msg)
                self.api_key_error_sent = True
            yield attempt

        else:
            translator = Translator(api_key)
            prompt = attempt.prompt
            attempt.notes["original_prompt"] = prompt
            for language in LOW_RESOURCE_LANGUAGES:
                attempt.notes["LRL_buff_dest_lang"] = language
                response = translator.translate_text(prompt, target_lang=language)
                translated_prompt = response.text
                attempt.prompt = translated_prompt
                yield self._derive_new_attempt(attempt)

    def untransform(self, attempt: garak.attempt.Attempt) -> garak.attempt.Attempt:
        api_key = getenv("DEEPL_API_KEY", None)
        translator = Translator(api_key)
        outputs = attempt.outputs
        attempt.notes["original_responses"] = outputs
        translated_outputs = list()
        for output in outputs:
            response = translator.translate_text(output, target_lang="EN-US")
            translated_output = response.text
            translated_outputs.append(translated_output)
        attempt.outputs = translated_outputs
        return attempt
