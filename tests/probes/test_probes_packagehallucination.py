import garak.probes.packagehallucination


def test_promptcount():
    p = garak.probes.packagehallucination.Python()
    assert len(p.prompts) == len(garak.probes.packagehallucination.stub_prompts) * len(
        garak.probes.packagehallucination.code_tasks
    )
