import pytest

import garak.probes.packagehallucination


@pytest.fixture
def p_config():
    return {"probes": {"packagehallucination": {"generations": 5}}}


def test_promptcount(p_config):
    p = garak.probes.packagehallucination.Python(config_root=p_config)
    assert len(p.prompts) == len(garak.probes.packagehallucination.stub_prompts) * len(
        garak.probes.packagehallucination.code_tasks
    )
