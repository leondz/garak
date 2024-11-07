# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _plugins

BUFFS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("buffs")
    if classname.startswith("buffs.paraphrase.")
]


@pytest.mark.parametrize("klassname", BUFFS)
def test_buff_results(klassname):
    b = _plugins.load_plugin(klassname)
    b._load_model()
    paraphrases = b._get_response("The rain in Spain falls mainly in the plains.")
    assert len(paraphrases) > 0, "paraphrase buffs must return paraphrases"
    assert len(paraphrases) == len(
        set(paraphrases)
    ), "Paraphrases should not have dupes"
    assert not any([i == "" for i in paraphrases]), "No paraphrase may be empty"
