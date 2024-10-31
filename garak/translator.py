# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0


""" Buff that paraphrases a prompt. """


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

# Ensure the NLTK words corpus is downloaded
nltk.download('words', quiet=True)

def remove_punctuation(text: str) -> str:
    punctuation_without_apostrophe = string.punctuation.replace("'", "")
    return ' '.join(char.replace(",", "") for char in text if char not in punctuation_without_apostrophe)


def is_english(text):
    """
    Determines if the given text is predominantly English based on word matching.

    Args:
        text (str): The text to evaluate.

    Returns:
        bool: True if more than 50% of the words are English, False otherwise.
    """
    # Load English words from NLTK
    english_words = set(words.words())
    
    text = text.lower()
    word_list = text.split()
    if len(word_list) == 0:
        return False

    if len(word_list) >= 1:
        word_list = remove_punctuation(word_list)
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

    def __init__(self, plugin_generators_dict: dict={}, source_lang: str="en") -> None:
        self.translator = None
        self.nmt_client = None
        self.translation_service = ""
        self.source_lang = source_lang
        self.target_lang = plugin_generators_dict.get("lang_spec", "en")
        self.translation_service = plugin_generators_dict.get("translation_service", "")
        self.model_name = plugin_generators_dict.get("translation_service", "")
        self.deepl_api_key = os.getenv(self.DEEPL_ENV_VAR)
        self.nim_api_key = os.getenv(self.NIM_ENV_VAR)

        if self.translation_service == "deepl" and not self.deepl_api_key:
            raise ValueError(f"{self.DEEPL_ENV_VAR} environment variable is not set")
        elif self.translation_service == "nim" and not self.nim_api_key:
            raise ValueError(f"{self.NIM_ENV_VAR} environment variable is not set")

        self.judge_list = []
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
            cleaned_line = remove_punctuation(line.strip().lower().split())
            if cleaned_line.isspace() or cleaned_line.replace("-", "") == "":
                translated_lines.append(cleaned_line)
                continue
            
            translated_line = self._translate(cleaned_line, source_lang=source_lang, target_lang=target_lang)
            translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res

    def translate_prompts(self, prompts: List[str]) -> List[str]:
        if hasattr(self, 'target_lang') is False or self.source_lang == "*" or self.target_lang == "":
            return prompts 
        translated_prompts = []
        prompts = list(prompts)
        for lang in self.target_lang.split(","):
            if self.source_lang == lang:
                continue 
            for prompt in prompts:
                mean_word_judge = is_english(prompt)
                self.judge_list.append(mean_word_judge)
                if mean_word_judge:
                    translate_prompt = self._get_response(prompt, self.source_lang, lang)
                    translated_prompts.append(translate_prompt)
                else:
                    translated_prompts.append(prompt)
        if len(translated_prompts) > 0:
            prompts.extend(translated_prompts)
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
                cleaned_sentence = remove_punctuation(sentence.strip().lower().split())
                if cleaned_sentence.isspace() or len(cleaned_sentence) == 0:
                    continue
                if cleaned_sentence in {".", "?", ". "}:
                    continue
                if cleaned_sentence.replace(".", "") == "":
                    continue
                translated_line = self._translate(cleaned_sentence, source_lang=source_lang, target_lang=target_lang)
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
            mean_word_judge = is_english(line) 

            if not mean_word_judge:
                translated_lines.append(line.strip())
            else:
                if "$" == line:
                    translated_lines.append(line)
                else:
                    line = remove_punctuation(line.lower().split())
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
                line = remove_punctuation(line.lower().split())
                translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res
    
class ReverseTranslator(SimpleTranslator):
    
    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            if self.translation_service == "deepl":
                return self.translator.translate_text(text, source_lang=target_lang, target_lang=source_lang).text
            elif self.translation_service == "nim":
                response = self.nmt_client.translate([text], "", target_lang, source_lang)
                return response.translations[0].text
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return text
    
    def translate_prompts(self, prompts):
        logging.debug(f"before reverses translated prompts : {prompts}")
        if hasattr(self, 'target_lang') is False or self.source_lang == "*" or self.target_lang == "":
            return prompts 
        translated_prompts = []
        prompts = list(prompts)
        for lang in self.target_lang.split(","):
            if self.source_lang == lang:
                continue 
            for prompt in prompts:
                mean_word_judge = is_meaning_string(prompt)
                self.judge_list.append(mean_word_judge)
                if mean_word_judge:
                    translate_prompt = self._get_response(prompt, self.source_lang, lang)
                    translated_prompts.append(translate_prompt)
                else:
                    translated_prompts.append(prompt)
        logging.debug(f"reverse translated prompts : {translated_prompts}")
        return translated_prompts 


class LocalTranslator():
    """Local translation using Huggingface m2m100 models
    Reference: 
      - https://huggingface.co/facebook/m2m100_1.2B 
      - https://huggingface.co/facebook/m2m100_418M
      - https://huggingface.co/docs/transformers/model_doc/marian
    """

    def __init__(self, plugin_generators_dict: dict={}, source_lang: str="en") -> None:
        self.device = torch.device("cpu" if not torch.cuda.is_available() else "cuda")
        self.source_lang = source_lang
        self.lang_specs = plugin_generators_dict.get("lang_spec", "en")
        self.target_lang = plugin_generators_dict.get("lang_spec", "en")
        self.model_name = plugin_generators_dict.get("local_model_name", "")
        self.tokenizer_name = plugin_generators_dict.get("local_tokenizer_name", "") 
        self.judge_list = []
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

    def _get_response(self, input_text: str, source_lang: Optional[str] = None, target_lang: Optional[list] = None):
        if not (source_lang and target_lang):
            return input_text

        translated_lines = []
        for line in input_text.splitlines():
            cleaned_line = remove_punctuation(line.strip().lower().split())
            if cleaned_line.isspace() or cleaned_line.replace("-", "") == "":
                translated_lines.append(cleaned_line)
                continue

            translated_line = self._translate(cleaned_line, source_lang=source_lang, target_lang=target_lang)
            translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)
        return res 
    
    def translate_prompts(self, prompts: List[str]) -> List[str]:
        if hasattr(self, 'target_lang') is False or self.source_lang == "*":
            return prompts 
        translated_prompts = []
        prompts = list(prompts)
        self.judge_list = []
        for lang in self.target_lang.split(","):
            if self.source_lang == lang:
                continue 
            for prompt in prompts:
                mean_word_judge = is_english(prompt)
                self.judge_list.append(mean_word_judge)
                if mean_word_judge:
                    translate_prompt = self._get_response(prompt, self.source_lang, lang)
                    translated_prompts.append(translate_prompt)
                else:
                    translated_prompts.append(prompt)
        if len(translated_prompts) > 0:
            prompts.extend(translated_prompts)
        logging.debug(f"prompts with translated prompts: {prompts}")
        return prompts 

    def translate_triggers(self, triggers):
        if is_nested_list(triggers):
            trigger_list = []
            for trigger in triggers:
                trigger_words = self.translate_prompts(trigger)
                for word in trigger_words:
                    trigger_list.append([word])
            return trigger_list
        else:
            return self.translate_prompts(triggers)


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
                cleaned_sentence = remove_punctuation(sentence.strip().lower().split())
                if cleaned_sentence.isspace() or len(cleaned_sentence) == 0:
                    continue
                if cleaned_sentence in {".", "?", ". "}:
                    continue
                if cleaned_sentence.replace(".", "") == "":
                    continue
                translated_line = self._translate(cleaned_sentence, source_lang=source_lang, target_lang=target_lang)
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
            mean_word_judge = is_english(line)

            if not mean_word_judge:
                translated_lines.append(line.strip())
            else:
                if "$" == line:
                    translated_lines.append(line)
                else:
                    line = remove_punctuation(line.lower().split())
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
                line = remove_punctuation(line.lower().split())
                translated_line = self._translate(line, source_lang=source_lang, target_lang=target_lang)
                translated_lines.append(translated_line)

        res = '\n'.join(translated_lines)

        return res


class LocalReverseTranslator(LocalTranslator):
    
    def __init__(self, plugin_generators_dict: dict={}, source_lang: str="en") -> None:
        self.device = torch.device("cpu" if not torch.cuda.is_available() else "cuda")
        self.source_lang = source_lang
        self.lang_specs = plugin_generators_dict.get("lang_spec", "en")
        self.target_lang = plugin_generators_dict.get("lang_spec", "en")
        self.model_name = plugin_generators_dict.get("local_model_name", "")
        self.tokenizer_name = plugin_generators_dict.get("local_tokenizer_name", "") 
        self._load_model()
        self.judge_list = []
    
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

    def translate_prompts(self, prompts):
        logging.debug(f"before reverses translated prompts : {prompts}")
        if hasattr(self, 'target_lang') is False or self.source_lang == "*":
            return prompts 
        translated_prompts = []
        prompts = list(prompts)
        for lang in self.target_lang.split(","):
            if self.source_lang == lang:
                continue 
            for prompt in prompts:
                mean_word_judge = is_meaning_string(prompt)
                self.judge_list.append(mean_word_judge)
                if mean_word_judge:
                    translate_prompt = self._get_response(prompt, self.source_lang, lang)
                    translated_prompts.append(translate_prompt)
                else:
                    translated_prompts.append(prompt)
        logging.debug(f"reverse translated prompts : {translated_prompts}")
        return translated_prompts 