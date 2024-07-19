import pytest
import transformers
import garak.generators.huggingface
from garak._config import GarakSubConfig

DEFAULT_GENERATIONS_QTY = 10


@pytest.fixture
def hf_generator_config():
    gen_config = {
        "huggingface": {
            "hf_args": {
                "device": "cpu",
                "torch_dtype": "float32",
            },
        }
    }
    config_root = GarakSubConfig()
    setattr(config_root, "generators", gen_config)
    return config_root


def test_pipeline(hf_generator_config):
    g = garak.generators.huggingface.Pipeline("gpt2", config_root=hf_generator_config)
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


def test_model(hf_generator_config):
    g = garak.generators.huggingface.Model("gpt2", config_root=hf_generator_config)
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
        assert item is None  # gpt2 is known raise exception returning `None`


def test_select_hf_device():
    from garak.generators.huggingface import HFCompatible
    import torch

    class mockHF(HFCompatible):
        def __init__(self, key, value):
            self.hf_args = {key: value}
            pass

    m = mockHF("device", -1)
    with pytest.raises(ValueError) as exc_info:
        device = m._select_hf_device()
    assert "CUDA device numbering starts" in str(exc_info.value)

    m = mockHF("device", "cpu")
    device = m._select_hf_device()
    assert device == torch.device("cpu")

    m = mockHF("device_map", "auto")
    device = m._select_hf_device()
    assert isinstance(device, torch.device)
