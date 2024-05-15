import garak.probes.encoding


def test_InjectBase64_len_cap():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.templates)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) < num_payloads * num_templates * num_encoders


def test_InjectBase64_prompt_trigger_match():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.templates)
    num_encoders = len(p.encoding_funcs)
    assert len(p.prompts) == len(p.triggers)


def test_InjectBase64_triggers_not_in_prompts():
    p = garak.probes.encoding.InjectBase64()
    num_payloads = len(garak.probes.encoding.payloads)
    num_templates = len(garak.probes.encoding.templates)
    num_encoders = len(p.encoding_funcs)
    for i in range(len(p.triggers)):
        assert p.triggers[i] not in p.prompts[i]
