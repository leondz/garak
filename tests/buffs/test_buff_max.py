from garak import _config
import garak._plugins
import garak.attempt


def test_buff_max_caps_items_returned_by_a_buff():
    _config.load_base_config()
    probe = garak._plugins.load_plugin("probes.test.Test")
    buff = garak._plugins.load_plugin("buffs.lowercase.Lowercase")
    _config.buffmanager.buffs = [buff]
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
    assert len(buffed) == 2
