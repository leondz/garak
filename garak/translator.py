# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0


""" Buff that paraphrases a prompt. """


from collections.abc import Iterable
import garak.attempt
from garak import _config
from typing import Optional
from deepl import Translator
import os
import riva.client
import enchant
import re
import unicodedata
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from transformers import MarianMTModel, MarianTokenizer
import torch
import string
import logging


def remove_punctuation(text: str) -> str:
    return ' '.join(char for char in text if char not in string.punctuation)


def is_english(text, clean_word_option=True):
    # Using an English dictionary
    d = enchant.Dict("en_US")
    text = text.lower()
    words = text.split()
    words = remove_punctuation(words)

    if text:
        if clean_word_option:
            cleaned_words = [''.join(char for char in word if char.isalnum()) for word in words.split(" ")]
        else:
            cleaned_words = words

        english_word_count = 0
        for word in cleaned_words:
            if "" == word:
                continue
            if d.check(word):
                english_word_count += 1
        logging.debug(f"Debug: english_word_count : {english_word_count}, words : {len(cleaned_words)}, {cleaned_words}")
        return english_word_count / len(cleaned_words) > 0.5
    return False


def split_input_text(input_text: str) -> list:
    """Split input text based on the presence of ': '."""
    if ": " in input_text:
        split_text = input_text.splitlines()
        split_text = [line.split(":") for line in split_text]
        split_text = [item for sublist in split_text for item in sublist]
    else:
        split_text = input_text.splitlines()
    return split_text


def contains_invisible_unicode(text: str) -> bool:
    """Determine whether the text contains invisible Unicode characters."""
    if not text:
        return False
    for char in text:
        if unicodedata.category(char) not in {'Cf', 'Cn', 'Zs'}:
            return False
    return True


class SimpleTranslator:
    """DeepL or NIM translation option"""

    # Reference: https://developers.deepl.com/docs/resources/supported-languages
    bcp47_deepl = [
        "ar", "bg", "cs", "da", "de",
        "en", "el", "es", "et", "fi",
        "fr", "hu", "id", "it", "ja",
        "ko", "lt", "lv", "nb", "nl",
        "pl", "pt", "ro", "ru", "sk",
        "sl", "sv", "tr", "uk", "zh"
    ]
    
    # Reference: https://docs.nvidia.com/nim/riva/nmt/latest/support-matrix.html#models
    bcp47_riva = [
        "zh", "ru", "de", "es", "fr",
        "da", "el", "fi", "hu", "it",
        "lt", "lv", "nl", "no", "pl",
        "pt", "ro", "sk", "sv", "ja",
        "hi", "ko", "et", "sl", "bg",
        "uk", "hr", "ar", "vi", "tr",
        "id", "cs"
    ]
    
    DEEPL_ENV_VAR = "DEEPL_API_KEY"
    NIM_ENV_VAR = "NIM_API_KEY"

    def __init__(self, config_root=_config) -> None:
        self.translator = None
        self.nmt_client = None
        self.translation_service = ""
        if hasattr(config_root, 'run'):
            self.translation_service = getattr(config_root.run, "translation_service", "")
        self.deepl_api_key = os.getenv(self.DEEPL_ENV_VAR)
        self.nim_api_key = os.getenv(self.NIM_ENV_VAR)

        if self.translation_service == "deepl" and not self.deepl_api_key:
            raise ValueError(f"{self.DEEPL_ENV_VAR} environment variable is not set")
        elif self.translation_service == "nim" and not self.nim_api_key:
            raise ValueError(f"{self.NIM_ENV_VAR} environment variable is not set")

        self._load_translator()

    def _load_translator(self):
        if self.translation_service == "deepl" and self.translator is None:
            self.translator = Translator(self.deepl_api_key)
        elif self.translation_service == "nim" and self.nmt_client is None:
            auth = riva.client.Auth(None, True, "grpc.nvcf.nvidia.com:443",
                                    [("function-id", "647147c1-9c23-496c-8304-2e29e7574510"),
                                     ("authorization", "Bearer " + self.nim_api_key)])
            self.nmt_client = riva.client.NeuralMachineTranslationClient(auth)

    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            if self.translation_service == "deepl":
                return self.translator.translate_text(text, source_lang=source_lang, target_lang=target_lang).text
            elif self.translation_service == "nim":
                response = self.nmt_client.translate([text], "", source_lang, target_lang)
                return response.translations[0].text
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return text

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):

        if not (source_lang and target_lang):
            return input_text

        translated_lines = []

        for line in input_text.splitlines():
            cleaned_line = line.strip()
            if cleaned_line.isspace() or cleaned_line.replace("-", "") == "":
                translated_lines.append(cleaned_line)
                continue
            
            cleaned_line_lower = cleaned_line.lower()
            translated_line = self._translate(cleaned_line_lower, source_lang=source_lang, target_lang=target_lang)
            translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res


class DanTranslator(SimpleTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):
        if not (source_lang and target_lang):
            return input_text

        self._load_translator()
        translated_lines = []

        for line in input_text.splitlines():
            if line.isspace() or line.strip().replace("-", "") == "":
                translated_lines.append(line)
                continue
            
            sentences = re.split(r'(\. |\?)', line.strip())
            for sentence in sentences:
                cleaned_sentence = sentence.strip()
                if cleaned_sentence.isspace() or len(cleaned_sentence) == 0:
                    continue
                if cleaned_sentence in {".", "?", ". "}:
                    continue
                if cleaned_sentence.replace(".", "") == "":
                    continue
                sentence = sentence.lower()
                translated_line = self._translate(sentence, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res


class EncodingTranslator(SimpleTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):

        if not (source_lang and target_lang):
            return input_text

        self._load_translator()
        translated_lines = []

        split_text = split_input_text(input_text)

        for line in split_text:
            mean_word_judge = is_english(line, clean_word_option=True)

            if not mean_word_judge:
                translated_lines.append(line.strip())
            else:
                if "$" == line:
                    translated_lines.append(line)
                else:
                    translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                    translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res

    
class GoodsideTranslator(SimpleTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):
        if not (source_lang and target_lang):
            return input_text

        self._load_translator()
        translated_lines = []

        for line in input_text.splitlines():

            if contains_invisible_unicode(line):
                translated_lines.append(line.strip())
            else:
                translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res
    

class LocalTranslator():
    """Local translation using Huggingface m2m100 models
    Reference: 
      - https://huggingface.co/facebook/m2m100_1.2B 
      - https://huggingface.co/facebook/m2m100_418M
      - https://huggingface.co/docs/transformers/model_doc/marian
    """

    def __init__(self, config_root=_config):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        lang_specs = getattr(config_root.run, 'lang_spec', "jap")  
        self.model_name = getattr(config_root.run, 'local_model_name', "Helsinki-NLP/opus-mt-en-{}")
        self.tokenizer_name = getattr(config_root.run, 'local_tokenizer_name', "Helsinki-NLP/opus-mt-en-{}")
        if "m2m100" in self.model_name:
            self.model = M2M100ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            self.tokenizer = M2M100Tokenizer.from_pretrained(self.tokenizer_name)
        else:
            self.models = {}
            self.tokenizers = {}
        
            for lang in lang_specs.split(","):
                model_name = self.model_name.format(lang)
                tokenizer_name = self.tokenizer_name.format(lang)
                self.models[lang] = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.tokenizers[lang] = MarianTokenizer.from_pretrained(tokenizer_name)

    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if "m2m100" in self.model_name:
            self.tokenizer.src_lang = source_lang
        
            encoded_text = self.tokenizer(text, return_tensors="pt").to(self.device)

            translated = self.model.generate(**encoded_text, forced_bos_token_id=self.tokenizer.get_lang_id(target_lang))

            translated_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        else:
            tokenizer = self.tokenizers[target_lang]
            model = self.models[target_lang]
            source_text = tokenizer.prepare_seq2seq_batch([text], return_tensors="pt").to(self.device)
            
            translated = model.generate(**source_text)
            
            translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]

        return translated_text

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[list] = None):
        if not (source_lang and target_lang):
            return input_text

        translated_lines = []
        for line in input_text.splitlines():
            cleaned_line = line.strip()
            if cleaned_line.isspace() or cleaned_line.replace("-", "") == "":
                translated_lines.append(cleaned_line)
                continue

            cleaned_line_lower = cleaned_line.lower()
            translated_line = self._translate(cleaned_line_lower, source_lang=source_lang, target_lang=target_lang)
            translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)
        return res 


class LocalDanTranslator(LocalTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):
        if not (source_lang and target_lang):
            return input_text

        translated_lines = []

        for line in input_text.splitlines():
            if line.isspace() or line.strip().replace("-", "") == "":
                translated_lines.append(line)
                continue
            
            sentences = re.split(r'(\. |\?)', line.strip())
            for sentence in sentences:
                cleaned_sentence = sentence.strip()
                if cleaned_sentence.isspace() or len(cleaned_sentence) == 0:
                    continue
                if cleaned_sentence in {".", "?", ". "}:
                    continue
                if cleaned_sentence.replace(".", "") == "":
                    continue
                sentence = sentence.lower()
                translated_line = self._translate(sentence, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res


class LocalEncodingTranslator(LocalTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):

        if not (source_lang and target_lang):
            return input_text

        translated_lines = []

        split_text = split_input_text(input_text)

        for line in split_text:
            mean_word_judge = is_english(line, clean_word_option=True)

            if not mean_word_judge:
                translated_lines.append(line.strip())
            else:
                if "$" == line:
                    translated_lines.append(line)
                else:
                    translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                    translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res


class LocalGoodsideTranslator(LocalTranslator):

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None):
        if not (source_lang and target_lang):
            return input_text

        translated_lines = []

        for line in input_text.splitlines():

            if contains_invisible_unicode(line):
                translated_lines.append(line.strip())
            else:
                translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res

