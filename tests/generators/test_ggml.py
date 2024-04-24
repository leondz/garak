import os
import pytest
import tempfile
import garak.generators.ggml

DEFAULT_GENERATIONS_QTY = 10

stored_env = os.getenv(garak.generators.ggml.ENV_VAR)
model_name = None


@pytest.fixture(autouse=True)
def reset_env(request) -> None:
    if stored_env is not None:
        os.environ[garak.generators.ggml.ENV_VAR] = stored_env
    model_name = tempfile.NamedTemporaryFile(suffix="_test_model.gguf")


@pytest.fixture(autouse=True)
def set_fake_env() -> None:
    os.environ[garak.generators.ggml.ENV_VAR] = os.path.abspath(__file__)


def test_init_bad_app():
    with pytest.raises(RuntimeError) as exc_info:
        if os.getenv(garak.generators.ggml.ENV_VAR) is not None:
            del os.environ[garak.generators.ggml.ENV_VAR]
        garak.generators.ggml.GgmlGenerator(model_name)
    assert "not provided by environment" in str(exc_info.value)


def test_init_missing_model():
    model_name = tempfile.TemporaryFile().name
    with pytest.raises(FileNotFoundError) as exc_info:
        garak.generators.ggml.GgmlGenerator(model_name)
    assert "File not found" in str(exc_info.value)


def test_init_bad_model():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_test_model.gguf", encoding="utf-8", delete=False
    ) as file:
        file.write(file.name)
        file.close()
        with pytest.raises(RuntimeError) as exc_info:
            garak.generators.ggml.GgmlGenerator(file.name)
        os.remove(file.name)
        assert "not in GGUF" in str(exc_info.value)


def test_init_good_model():
    with tempfile.NamedTemporaryFile(suffix="_test_model.gguf", delete=False) as file:
        file.write(garak.generators.ggml.GGUF_MAGIC)
        file.close()
        g = garak.generators.ggml.GgmlGenerator(file.name)
        os.remove(file.name)
        assert type(g) is garak.generators.ggml.GgmlGenerator
