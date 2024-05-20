from dataclasses import dataclass
from garak import _config
from garak import _plugins


@dataclass
class ConfigurationParameter:
    required = False
    name = None
    default = None


class Configurable:
    # instance variable to allow early load or load from `base.py`
    loaded = False

    def _supported_configs() -> list[ConfigurationParameter]:
        return []

    def _load_config(self, config_root=_config):
        local_root = (
            config_root.plugins if hasattr(config_root, "plugins") else config_root
        )
        classname = self.__class__.__name__
        namespace_parts = self.__module__.split(".")
        spec_type = namespace_parts[-2]
        namespace = namespace_parts[-1]
        apply_for = [namespace, f"{namespace}.{classname}"]
        # last part is the namespace, second to last is the plugin type
        # think about how to make this abstract enough to support something like
        # plugins['detectors'][x]['generators']['rest.RestGenerator']
        # plugins['detectors'][x]['generators']['rest']
        # plugins['probes'][y]['generators']['rest.RestGenerator']
        if len(namespace_parts) > 2:
            # example class expected garak.generators.huggingface.Pipeline
            # spec_type = generators
            # namespace = huggingface
            # classname = Pipeline

            if hasattr(local_root, spec_type):
                # make this adaptive default is `plugins`
                plugins_config = getattr(
                    local_root, spec_type
                )  # expected values `probes/detectors/buffs/generators/harnesses` possibly get this list at runtime
                for apply in apply_for:
                    if apply in plugins_config:
                        # expected values:
                        # generators: `nim/openai/huggingface`
                        # probes: `dan/gcg/xss/tap/promptinject`
                        # possibly get this list at runtime
                        for k, v in plugins_config[apply].items():
                            # this should probably execute recursively for, think more...
                            # should we support qualified hierarchy or only parent & concrete?
                            if (
                                k in _plugins.PLUGIN_TYPES
                            ):  # skip items for more qualified items, also skip reference to any plugin type
                                continue
                            setattr(
                                self, k, v
                            )  # consider expanding this to deep set values such as [config][device_map]
        self.loaded = True
