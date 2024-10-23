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
    LocalReverseTranslator,
    split_input_text
)
from garak import _config
import os
from garak.generators.nim import NVOpenAIChat
import importlib
import garak


NIM_ENV_VAR = "NIM_API_KEY"
DEEPL_ENV_VAR = "DEEPL_API_KEY"


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
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_local_translate_single_language(translator_class, lang_spec, model_name, tokenizer_name):
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["lang_spec"] = lang_spec 
    _config.plugins.generators["local_model_name"] = model_name 
    _config.plugins.generators["local_tokenizer_name"] = tokenizer_name 
    translator = translator_class(_config.plugins.generators)
    input_text = "Hello, how are you?"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang=lang_spec)
    assert isinstance(translated_text, str)
    assert translated_text != input_text
    importlib.reload(garak._config)
    garak._config.load_base_config()


@pytest.mark.parametrize("translator_class, lang_specs, model_name, tokenizer_name", [
    (LocalTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalDanTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B" ),
    (LocalEncodingTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B" ),
    (LocalGoodsideTranslator, ["ja", "fr"], "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalDanTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalEncodingTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalGoodsideTranslator, ["jap", "fr"], "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
])
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_local_translate_multiple_languages(translator_class, lang_specs, model_name, tokenizer_name):
    input_text = "Hello, how are you?"
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["local_model_name"] = model_name 
    _config.plugins.generators["local_tokenizer_name"] = tokenizer_name 
    
    for lang_spec in lang_specs:
        _config.plugins.generators["lang_spec"] = lang_spec 
        translator = translator_class(_config.plugins.generators)
        translated_text = translator._get_response(input_text, 
            source_lang="en", 
            target_lang=lang_spec)
        assert isinstance(translated_text, str)
        assert translated_text != input_text
    importlib.reload(garak._config)
    garak._config.load_base_config()

@pytest.mark.parametrize("translator_class, model_name, tokenizer_name", [
    (LocalTranslator, "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalDanTranslator, "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalEncodingTranslator, "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalGoodsideTranslator, "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, "facebook/m2m100_1.2B", "facebook/m2m100_1.2B"),
    (LocalTranslator, "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalDanTranslator, "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalEncodingTranslator, "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
    (LocalGoodsideTranslator, "Helsinki-NLP/opus-mt-en-{}", "Helsinki-NLP/opus-mt-en-{}"),
])
@pytest.mark.requires_storage(required_space_gb=2, path="/")
def test_same_source_and_target_language(translator_class, model_name, tokenizer_name):
    input_text = ["Hello, how are you?"]
    _config.plugins.generators["translation_service"] = 'local'
    _config.plugins.generators["local_model_name"] = model_name 
    _config.plugins.generators["local_tokenizer_name"] = tokenizer_name 
    _config.plugins.generators["lang_spec"] = "en" 
    
    translator = LocalTranslator(_config.plugins.generators)
    translated_text = translator.translate_prompts(input_text) 
    
    assert translated_text == input_text, "Translation should be the same as input when source and target languages are identical"
    importlib.reload(garak._config)
    garak._config.load_base_config()

@pytest.mark.parametrize("model_name, tokenizer_name, lang", [
    ("facebook/m2m100_1.2B", "facebook/m2m100_1.2B", "ja"),
    ("Helsinki-NLP/opus-mt-{}-en", "Helsinki-NLP/opus-mt-{}-en", "jap"),
])
def test_reverse_translation(model_name, tokenizer_name, lang):
    input_text = ["こんにちは。調子はどうですか?"]
    _config.plugins.generators["lang_spec"] = lang
    _config.plugins.generators["local_model_name"] = model_name 
    _config.plugins.generators["local_tokenizer_name"] = tokenizer_name 
    translator = LocalReverseTranslator(_config.plugins.generators)
    
    translated_text = translator.translate_prompts(input_text) 
    
    assert translated_text[0] != input_text[0], "Translation should be the different as input when source and target languages are identical"

@pytest.fixture(params=[
    (SimpleTranslator, "ja"),
    (DanTranslator, "ja"),
    (EncodingTranslator, "ja"),
    (GoodsideTranslator, "ja"),
])
def translator(request):
    translator_class, lang_spec = request.param
    _config.plugins.generators["translation_service"] = "nim"
    _config.plugins.generators["lang_spec"] = lang_spec 
    return translator_class(_config.plugins.generators)


@pytest.mark.skipif(
    os.getenv(NIM_ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NIM_ENV_VAR}",
)
def test_nim_translate_single_language(translator):
    input_text = "Hello, how are you?"
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang="ja")
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.skipif(
    os.getenv(NIM_ENV_VAR, None) is None,
    reason=f"NIM API key is not set in {NIM_ENV_VAR}",
)
@pytest.mark.parametrize("lang_spec", ["ja", "fr"])
def test_nim_translate_multiple_languages(translator, lang_spec):
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
def test_deepl_translate_single_language(translator):
    input_text = "Hello, how are you?"
    _config.plugins.generators["translation_service"] = "deepl"
    _config.plugins.generators["lang_spec"] = "ja" 
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang="ja")
    assert isinstance(translated_text, str)
    assert translated_text != input_text


@pytest.mark.skipif(
    os.getenv(DEEPL_ENV_VAR, None) is None,
    reason=f"DeepL API key is not set in {DEEPL_ENV_VAR}",
)
@pytest.mark.parametrize("lang_spec", ["ja", "fr"])
def test_deepl_translate_multiple_languages(translator, lang_spec):
    input_text = "Hello, how are you?"
    translator.translation_service = "deepl"
    _config.plugins.generators["translation_service"] = "deepl"
    _config.plugins.generators["lang_spec"] = "ja" 
    
    translated_text = translator._get_response(input_text, 
        source_lang="en", 
        target_lang="ja")
    assert isinstance(translated_text, str)
    assert translated_text != input_text