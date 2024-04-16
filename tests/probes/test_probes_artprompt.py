#!/usr/bin/env python3

import garak.probes.artprompt


# one or more prompts are created for each stub
def test_prompts_block():
    p = garak.probes.artprompt.Block()
    num_stubs = len(garak.probes.artprompt.stub_prompts)
    assert len(p.prompts) >= num_stubs

# one or more prompts are created for each stub
def test_prompts_cards():
    p = garak.probes.artprompt.Cards()
    num_stubs = len(garak.probes.artprompt.stub_prompts)
    assert len(p.prompts) >= num_stubs

# ensure all `safety_words` are masked in generated prompts
def test_prompts_masking():
    p = garak.probes.artprompt.Block()
    for prompt in p.prompts:
        for word in garak.probes.artprompt.safety_words:
            assert prompt.count(word) == 0
