from collections import Counter

from garak import _config
import garak._plugins
import garak.attempt


def test_buff_max_caps_buffed_attempts_per_prompt():
    _config.load_base_config()
    probe = garak._plugins.load_plugin("probes.test.Test")
    buffs = [
        garak._plugins.load_plugin(name)
        for name in (
            "buffs.lowercase.Lowercase",
            "buffs.encoding.Base64",
            "buffs.encoding.CharCode",
        )
    ]
    _config.buffmanager.buffs = buffs
    _config.plugins.buffs_include_original_prompt = False
    _config.plugins.buff_max = 2
    try:
        attempts = [
            probe._mint_attempt(f"Prompt {i}", seq=i, lang="en") for i in range(5)
        ]
        buffed = list(probe._buff_hook(attempts))
    finally:
        _config.buffmanager.buffs = []
        _config.plugins.buff_max = None
    # every prompt gets buff_max buffed variants, from the first buffs in order
    assert Counter(a.seq for a in buffed) == {i: 2 for i in range(5)}
    assert len(buffed) == 10
