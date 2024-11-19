import pytest

from garak.resources import fixer
from garak import _config

BASE_TEST_CONFIG = """
---
plugins:
  probe_spec: test.Test
"""


@pytest.fixture
def inject_custom_config(request, pre_migration_dict):
    import tempfile
    import yaml

    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
        filename = tmp.name
        config_dict = yaml.safe_load(BASE_TEST_CONFIG)
        config_dict["plugins"] = config_dict["plugins"] | pre_migration_dict
        yaml.dump(config_dict, tmp)
        tmp.close()

    def remove_test_file():
        import os

        files = [filename]
        for file in files:
            if os.path.exists(file):
                os.remove(file)

    request.addfinalizer(remove_test_file)

    return filename


@pytest.mark.parametrize(
    "migration_name, pre_migration_dict, post_migration_dict",
    [
        (
            None,
            {},
            {"probe_spec": "test.Test"},
        ),
        (
            "RenameGCG",
            {
                "probe_spec": "lmrc,gcg,tap",
            },
            {
                "probe_spec": "lmrc,suffix,tap",
            },
        ),
        (
            "RenameGCG",
            {
                "probe_spec": "lmrc,gcg,tap",
                "probes": {"gcg": {"GOAL": "fake the goal"}},
            },
            {
                "probe_spec": "lmrc,suffix,tap",
                "probes": {"suffix": {"GOAL": "fake the goal"}},
            },
        ),
        (
            "RenameGCG",
            {
                "probe_spec": "lmrc,gcg.GCGCached,tap",
                "probes": {
                    "gcg": {
                        "GCGCached": {},
                        "GOAL": "fake the goal",
                    }
                },
            },
            {
                "probe_spec": "lmrc,suffix.GCGCached,tap",
                "probes": {
                    "suffix": {
                        "GCGCached": {},
                        "GOAL": "fake the goal",
                    }
                },
            },
        ),
        (
            "RenameContinuation",
            {
                "probe_spec": "lmrc,continuation.ContinueSlursReclaimedSlurs80,tap",
            },
            {
                "probe_spec": "lmrc,continuation.ContinueSlursReclaimedSlursMini,tap",
            },
        ),
        (
            "RenameContinuation",
            {
                "probe_spec": "lmrc,continuation,tap",
                "probes": {
                    "continuation": {
                        "ContinueSlursReclaimedSlurs80": {
                            "source_resource_filename": "fake_data_file.json"
                        }
                    }
                },
            },
            {
                "probe_spec": "lmrc,continuation,tap",
                "probes": {
                    "continuation": {
                        "ContinueSlursReclaimedSlursMini": {
                            "source_resource_filename": "fake_data_file.json"
                        }
                    }
                },
            },
        ),
        (
            "RenameKnownbadsignatures",
            {
                "probe_spec": "knownbadsignatures.EICAR,lmrc,tap",
            },
            {
                "probe_spec": "av_spam_scanning.EICAR,lmrc,tap",
            },
        ),
        (
            "RenameKnownbadsignatures",
            {
                "probe_spec": "knownbadsignatures,lmrc,tap",
            },
            {
                "probe_spec": "av_spam_scanning,lmrc,tap",
            },
        ),
        (
            "RenameReplay",
            {
                "probe_spec": "lmrc,tap,replay",
            },
            {
                "probe_spec": "lmrc,tap,divergence",
            },
        ),
        (
            "RenameReplay",
            {
                "probe_spec": "lmrc,tap,replay.Repeat",
            },
            {
                "probe_spec": "lmrc,tap,divergence.Repeat",
            },
        ),
    ],
)
def test_fixer_migrate(
    mocker,
    inject_custom_config,
    migration_name,
    post_migration_dict,
):
    import logging

    mock_log_info = mocker.patch.object(
        logging,
        "info",
    )
    revised_config = fixer.migrate(inject_custom_config)
    assert revised_config["plugins"] == post_migration_dict
    if migration_name is None:
        assert (
            not mock_log_info.called
        ), "Logging should not be called when no migrations are applied"
    else:
        # expect `migration_name` in a log call via mock of logging.info()
        assert "Migration preformed" in mock_log_info.call_args.args[0]
        found_class = False
        for calls in mock_log_info.call_args_list:
            found_class = migration_name in calls.args[0]
            if found_class:
                break
        assert found_class
