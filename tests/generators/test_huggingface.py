import transformers
import garak.generators.huggingface

DEFAULT_GENERATIONS_QTY = 10


def test_pipeline():
    g = garak.generators.huggingface.Pipeline("gpt2")
    assert g.name == "gpt2"
    assert g.generations == DEFAULT_GENERATIONS_QTY
    assert isinstance(g.generator, transformers.pipelines.text_generation.Pipeline)
    assert isinstance(g.generator.model, transformers.PreTrainedModel)
    assert isinstance(g.generator.tokenizer, transformers.PreTrainedTokenizerBase)
    assert isinstance(g.max_tokens, int)
    g.max_tokens = 99
    assert g.max_tokens == 99
    g.temperature = 0.1
    assert g.temperature == 0.1
    output = g.generate("")
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)


def test_inference():
    return  # slow w/o key
    g = garak.generators.huggingface.InferenceAPI("gpt2")
    assert g.name == "gpt2"
    assert g.generations == DEFAULT_GENERATIONS_QTY
    assert isinstance(g.max_tokens, int)
    g.max_tokens = 99
    assert g.max_tokens == 99
    g.temperature = 0.1
    assert g.temperature == 0.1
    output = g.generate("")
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)


def test_model():
    g = garak.generators.huggingface.Model("gpt2")
    assert g.name == "gpt2"
    assert g.generations == DEFAULT_GENERATIONS_QTY
    assert isinstance(g, garak.generators.huggingface.Model)
    assert isinstance(g.model, transformers.PreTrainedModel)
    assert isinstance(g.tokenizer, transformers.PreTrainedTokenizerBase)
    assert isinstance(g.max_tokens, int)
    g.max_tokens = 99
    assert g.max_tokens == 99
    g.temperature = 0.1
    assert g.temperature == 0.1
    output = g.generate("")
    assert len(output) == DEFAULT_GENERATIONS_QTY
    for item in output:
        assert isinstance(item, str)
