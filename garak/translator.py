# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0


""" Translator that translates a prompt. """


from collections.abc import Iterable
import garak.attempt
from typing import Optional, List
from deepl import Translator
import os
import riva.client
import re
import unicodedata
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from transformers import MarianMTModel, MarianTokenizer
import torch
import string
import logging
import nltk
from nltk.corpus import words
from langdetect import detect, DetectorFactory, LangDetectException
from garak import _config
import json

# Ensure the NLTK words corpus is downloaded
nltk.download('words', quiet=True)


def remove_english_punctuation(text: str) -> str:
    punctuation_without_apostrophe = string.punctuation.replace("'", "")
    return ' '.join(re.sub(":|,", "", char) for char in text if char not in punctuation_without_apostrophe)


def is_english(text):
    """
    Determines if the given text is predominantly English based on word matching.

    Args:
        text (str): The text to evaluate.

    Returns:
        bool: True if more than 50% of the words are English, False otherwise.
    """
    # Load English words from NLTK
    special_terms = {"ascii85", "encoded", "decoded", "acsii", "plaintext"}
    english_words = set(words.words()).union(special_terms)
    
    text = text.lower()
    word_list = text.split()
    if len(word_list) == 0:
        return False

    if len(word_list) >= 1:
        word_list = remove_english_punctuation(word_list)
    else:
        word_list = word_list[0]

    if word_list:
        word_list = word_list.split()
        cleaned_words = ' '.join(char for char in word_list if char.isalpha())
        # Filter out empty strings
        cleaned_words = cleaned_words.split()
        cleaned_words = [word for word in cleaned_words if word]

        if not cleaned_words:
            return False

        english_word_count = sum(1 for word in cleaned_words if word in english_words)
        return (english_word_count / len(cleaned_words)) > 0.5
    return False


def split_input_text(input_text: str) -> list:
    """Split input text based on the presence of ': '."""
    if ": " in input_text and "http://" not in input_text and "https://" not in input_text: 
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


def is_nested_list(lst: list) -> bool:
    """Check if the given list is a nested list."""
    return any(isinstance(i, list) for i in lst)


def is_meaning_string(text: str) -> bool:
    """Check if the input text is a meaningless sequence or invalid for translation."""
    DetectorFactory.seed = 0

    # Detect Language: Skip if no valid language is detected
    try:
        lang = detect(text)
        logging.debug(f"Detected language: {lang} text {text}")
    except LangDetectException:
        logging.debug("Could not detect a valid language.")
        return False 
    
    if lang == "en":
        return False

    # Length and pattern checks: Skip if it's too short or repetitive
    if len(text) < 3 or re.match(r"(.)\1{3,}", text):  # e.g., "aaaa" or "123123"
        logging.debug(f"Detected short or repetitive sequence. text {text}")
        return False 

    return True 


def convert_json_string(json_string):
    # Replace single quotes with double quotes
    json_string = re.sub(r"'", '"', json_string)
    
    # Replace True with true
    json_string = re.sub('True', 'true', json_string)
    
    # Replace False with false
    json_string = re.sub('False', 'false', json_string)
    
    return json_string


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

    def __init__(self, config_root: _config=_config, source_lang: str="en") -> None:
        self.translator = None
        self.nmt_client = None
        self.translation_service = ""
        self.source_lang = source_lang
        self.translation_service = config_root.run.translation['translation_service']
        self.target_lang = config_root.run.translation['lang_spec']
        self.model_name = config_root.run.translation['model_spec']['model_name']
        if self.translation_service == "deepl":
            self.deepl_api_key = config_root.run.translation['api_key']
        if self.translation_service == "nim":
            self.nim_api_key = config_root.run.translation['api_key']

        if self.translation_service == "deepl" and not self.deepl_api_key:
            raise ValueError(f"{self.deepl_api_key} environment variable is not set")
        elif self.translation_service == "nim" and not self.nim_api_key:
            raise ValueError(f"{self.nim_api_key} environment variable is not set")

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

        if source_lang is None or target_lang is None:
            return input_text

        translated_lines = []
        
        split_text = split_input_text(input_text)

        for line in split_text:
            if self._should_skip_line(line):
                if contains_invisible_unicode(line):
                    continue
                translated_lines.append(line.strip())
                continue
            if contains_invisible_unicode(line):
                continue
            if len(line) <= 200:
                translated_lines = self._short_sentence_translate(line, 
                    source_lang=source_lang, 
                    target_lang=target_lang, 
                    translated_lines=translated_lines
                    )
            else:
                translated_lines = self._long_sentence_translate(line, 
                    source_lang=source_lang, 
                    target_lang=target_lang, 
                    translated_lines=translated_lines
                    )

        return '\n'.join(translated_lines)
    
    def _short_sentence_translate(self, line: str, 
        source_lang: str, target_lang: str, translated_lines: list) -> str:
        if "Reverse" in self.__class__.__name__:
            cleaned_line = self._clean_line(line)
            if cleaned_line:
                translated_line = self._translate(cleaned_line, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)
        else:
            mean_word_judge = is_english(line) 
            if not mean_word_judge or line == "$": 
                translated_lines.append(line.strip())
            else:
                cleaned_line = self._clean_line(line)
                if cleaned_line:
                    translated_line = self._translate(cleaned_line, source_lang=source_lang, target_lang=target_lang)
                    translated_lines.append(translated_line)
        
        return translated_lines
    
    def _long_sentence_translate(self, line: str, 
        source_lang: str, target_lang: str, translated_lines: list) -> str:
        sentences = re.split(r'(\. |\?)', line.strip())
        for sentence in sentences:
            cleaned_sentence = self._clean_line(sentence)
            if self._should_skip_line(cleaned_sentence):
                translated_lines.append(cleaned_sentence)
                continue
            translated_line = self._translate(cleaned_sentence, source_lang=source_lang, target_lang=target_lang)
            translated_lines.append(translated_line)
        
        return translated_lines

    def _should_skip_line(self, line: str) -> bool:
        return line.isspace() or line.strip().replace("-", "") == "" or \
            len(line) == 0 or line.replace(".", "") == "" or line in {".", "?", ". "}

    def _clean_line(self, line: str) -> str:
        return remove_english_punctuation(line.strip().lower().split())

    def translate_prompts(self, prompts: List[str], only_translate_word: bool=False, reverse_translate_judge: bool=False) -> List[str]:
        if hasattr(self, 'target_lang') is False or self.source_lang == "*" or self.target_lang == "":
            return prompts 
        translated_prompts = []
        prompts = list(prompts)
        self.lang_list = []
        for i in range(len(prompts)):
            self.lang_list.append(self.source_lang)
        for lang in self.target_lang.split(","):
            if self.source_lang == lang:
                continue 
            for prompt in prompts:
                if reverse_translate_judge:
                    mean_word_judge = is_meaning_string(prompt)
                    if mean_word_judge:
                        translate_prompt = self._get_response(prompt, self.source_lang, lang)
                        translated_prompts.append(translate_prompt)
                    else:
                        translated_prompts.append(prompt)
                else:
                    translate_prompt = self._get_response(prompt, self.source_lang, lang)
                    translated_prompts.append(translate_prompt)
                self.lang_list.append(lang)
        if len(translated_prompts) > 0:
            prompts.extend(translated_prompts)
        if only_translate_word:
            logging.debug(f"prompts with translated translated_prompts: {translated_prompts}")
            return translated_prompts
        logging.debug(f"prompts with translated prompts: {prompts}")
        return prompts

    def translate_triggers(self, triggers: list):
        if is_nested_list(triggers):
            trigger_list = []
            for trigger in triggers:
                trigger_words = self.translate_prompts(trigger)
                for word in trigger_words:
                    trigger_list.append([word])
            triggers = trigger_list 
            return triggers
        else:
            triggers = self.translate_prompts(triggers)
            return triggers
    
    def translate_descr(self, attempt_descrs: List[str]) -> List[str]:
        translated_attempt_descrs = []
        for descr in attempt_descrs:
            descr = json.loads(convert_json_string(descr))
            if type(descr["prompt_stub"]) is list:
                translate_prompt_stub = self.translate_prompts(descr["prompt_stub"], only_translate_word=True)
            else:
                translate_prompt_stub = self.translate_prompts([descr["prompt_stub"]], only_translate_word=True)
            if type(descr["payload"]) is list:
                translate_payload = self.translate_prompts(descr["payload"], only_translate_word=True)
            else:
                translate_payload = self.translate_prompts([descr["payload"]], only_translate_word=True)
            translated_attempt_descrs.append(
                str(
                    {
                        "prompt_stub": translate_prompt_stub,
                        "distractor": descr["distractor"],
                        "payload": translate_payload,
                        "az_only": descr["az_only"],
                        "use refocusing statement": descr["use refocusing statement"], 
                    }
                )
            )
        return translated_attempt_descrs


class ReverseTranslator(SimpleTranslator):
    
    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            if self.translation_service == "deepl":
                source_lang = "en-us"
                return self.translator.translate_text(text, source_lang=target_lang, target_lang=source_lang).text
            elif self.translation_service == "nim":
                response = self.nmt_client.translate([text], "", target_lang, source_lang)
                return response.translations[0].text
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return text
    

class LocalHFTranslator(SimpleTranslator):
    """Local translation using Huggingface m2m100 models
    Reference: 
      - https://huggingface.co/facebook/m2m100_1.2B 
      - https://huggingface.co/facebook/m2m100_418M
      - https://huggingface.co/docs/transformers/model_doc/marian
    """

    def __init__(self, config_root: _config=_config, source_lang: str="en") -> None:
        self.device = torch.device("cpu" if not torch.cuda.is_available() else "cuda")
        self.source_lang = source_lang
        self.lang_specs = config_root.run.translation['lang_spec']
        self.target_lang = config_root.run.translation['lang_spec']
        self.model_name = config_root.run.translation['model_spec']['model_name']
        self.tokenizer_name = config_root.run.translation['model_spec']['model_name'] 
        self._load_model()
    
    def _load_model(self):
        if "m2m100" in self.model_name and self.target_lang != "en":
            self.model = M2M100ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            self.tokenizer = M2M100Tokenizer.from_pretrained(self.tokenizer_name)
        else:
            self.models = {}
            self.tokenizers = {}
        
            for lang in self.lang_specs.split(","):
                if lang != "en":
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
            
            return translated_text
        else:
            tokenizer = self.tokenizers[target_lang]
            model = self.models[target_lang]
            source_text = tokenizer.prepare_seq2seq_batch([text], return_tensors="pt").to(self.device)
            
            translated = model.generate(**source_text)
            
            translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]

            return translated_text


class LocalHFReverseTranslator(LocalHFTranslator):
    
    def __init__(self, config_root: _config=_config, source_lang: str="en") -> None:
        super().__init__(config_root, source_lang)
        self._load_model()
    
    def _load_model(self):
        if "m2m100" in self.model_name:
            self.model = M2M100ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            self.tokenizer = M2M100Tokenizer.from_pretrained(self.tokenizer_name)
        else:
            self.models = {}
            self.tokenizers = {}
        
            for lang in self.lang_specs.split(","):
                model_name = self.model_name.format(lang)
                tokenizer_name = self.tokenizer_name.format(lang)
                self.models[lang] = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.tokenizers[lang] = MarianTokenizer.from_pretrained(tokenizer_name)

    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if "m2m100" in self.model_name:
            self.tokenizer.src_lang = target_lang
        
            encoded_text = self.tokenizer(text, return_tensors="pt").to(self.device)

            translated = self.model.generate(**encoded_text, forced_bos_token_id=self.tokenizer.get_lang_id(source_lang))

            translated_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
        else:
            tokenizer = self.tokenizers[target_lang]
            model = self.models[target_lang]
            source_text = tokenizer.prepare_seq2seq_batch([text], return_tensors="pt").to(self.device)
            
            translated = model.generate(**source_text)
            
            translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True)[0]

        return translated_text
    

def load_translator(translation_service: str="", classname: str="") -> object:
    translator_instance = None
    logging.debug(f"translation_service: {translation_service} classname: {classname}")
    if translation_service == "local":
        if classname == "reverse":
            translator_instance = LocalHFReverseTranslator()
        else:
            translator_instance = LocalHFTranslator()
    elif translation_service == "deepl" or translation_service == "nim":
        if classname == "reverse":
            translator_instance = ReverseTranslator()
        else:
            translator_instance = SimpleTranslator()
    return translator_instance
