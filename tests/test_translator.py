import pytest
from garak.translator import (
    SimpleTranslator,
    DanTranslator,
    EncodingTranslator,
    GoodsideTranslator,
    LocalTranslator,
    LocalDanTranslator,
    LocalEncodingTranslator,
    LocalGoodsideTranslator,
    split_input_text
)
from garak import _config
import os
from garak.generators.nim import NVOpenAIChat


NIM_ENV_VAR = "NIM_API_KEY"
DEEPL_ENV_VAR = "DEEPL_API_KEY"


@pytest.fixture
def config():
    config = _config
    return config


def test_split_input_text():
    input_text = "Hello: How are you?\nI am fine: Thank you."
    expected_output = ["Hello", " How are you?", "I am fine", " Thank you."]
    assert split_input_text(input_text) == expected_output

    input_text = "Hello\nHow are you?\nI am fine\nThank you."
    expected_output = ["Hello", "How are you?", "I am fine", "Thank you."]
    assert split_input_text(input_text) == expected_output


@pytest.mark.parametrize("translator_class, lang_spec, model_name, tokenizer_name", [
    (LocalTranslator, "ja", "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalDanTranslator, "ja", "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalEncodingTranslator, "ja", "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalGoodsideTranslator, "ja", "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, "fr", "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, "jap", "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalDanTranslator, "jap", "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalEncodingTranslator, "jap", "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalGoodsideTranslator, "jap", "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalTranslator, "fr", "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
])
def test_local_translate_single_language(translator_class, lang_spec, model_name, tokenizer_name):
    config = _config
    config.run.local_model_name = model_name 
    config.run.local_tokenizer_name = tokenizer_name 
    config.run.lang_spec = lang_spec
    translator = translator_class(config_root=config)
    input_text = "Hello, how are you?"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=config.run.lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.parametrize("translator_class, lang_specs, model_name, tokenizer_name", [
    (LocalTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalDanTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalEncodingTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalGoodsideTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalDanTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalEncodingTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalGoodsideTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
])
def test_local_translate_multiple_languages(translator_class, lang_specs, model_name, tokenizer_name):
    config = _config
    input_text = "Hello, how are you?"
    config.run.local_model_name = model_name 
    config.run.local_tokenizer_name = tokenizer_name 
    
    for lang_spec in lang_specs:
        config.run.lang_spec = lang_spec
        translator = translator_class(config_root=config)
        translated_text = translator._get_response(input_text, 
            source_lang="en", 
            target_lang=lang_spec)
        assert isinstance(translated_text, str)
        assert translated_text != input_text


@pytest.fixture(params=[
    (SimpleTranslator, "ja"),
    (DanTranslator, "ja"),
    (EncodingTranslator, "ja"),
    (GoodsideTranslator, "ja"),
])
def translator(request, config):
    translator_class, lang_spec = request.param
    config.run.translation_service = "nim"
    config.run.lang_spec = lang_spec
    return translator_class(config_root=config)


@pytest.mark.skipif(
    os.getenv(NIM_ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NIM_ENV_VAR}",
)
def test_nim_translate_single_language(translator, config):
    input_text = "Hello, how are you?"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=config.run.lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.skipif(
    os.getenv(NIM_ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NIM_ENV_VAR}",
)
@pytest.mark.parametrize("lang_spec", ["ja", "fr"])
def test_nim_translate_multiple_languages(translator, config, lang_spec):
    input_text = "Hello, how are you?"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.skipif(
    os.getenv(DEEPL_ENV_VAR, None) is None,
    reason=f"DeepL API key is not set in {DEEPL_ENV_VAR}",
)
def test_deepl_translate_single_language(translator, config):
    input_text = "Hello, how are you?"
    translator.translation_service = "deepl"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=config.run.lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.skipif(
    os.getenv(DEEPL_ENV_VAR, None) is None,
    reason=f"DeepL API key is not set in {DEEPL_ENV_VAR}",
)
@pytest.mark.parametrize("lang_spec", ["ja", "fr"])
def test_deepl_translate_multiple_languages(translator, config, lang_spec):
    input_text = "Hello, how are you?"
    translator.translation_service = "deepl"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text