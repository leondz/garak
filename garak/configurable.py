import logging
from dataclasses import dataclass
from garak import _config
from garak import _plugins


class Configurable:
    # instance variable to allow early load or load from `base.py`
    loaded = False

    def _load_config(self, config_root=_config):
        local_root = (
            config_root.plugins if hasattr(config_root, "plugins") else config_root
        )
        namespace_parts = self.__module__.split(".")
        # last part is the namespace, second to last is the plugin type
        # this will support something like:
        # plugins['detectors'][x]['generators']['rest']['RestGenerator']
        # plugins['detectors'][x]['generators']['rest']
        # plugins['probes'][y]['generators']['rest']['RestGenerator']
        if len(namespace_parts) > 2:
            # example class expected garak.generators.huggingface.Pipeline
            # spec_type = generators
            # namespace = huggingface
            # classname = Pipeline
            spec_type = namespace_parts[-2]
            namespace = namespace_parts[-1]
            classname = self.__class__.__name__
            if hasattr(local_root, spec_type):
                plugins_config = getattr(
                    local_root, spec_type
                )  # expected values `probes/detectors/buffs/generators/harnesses` possibly get this list at runtime
                if namespace in plugins_config:
                    # example values:
                    # generators: `nim/openai/huggingface`
                    # probes: `dan/gcg/xss/tap/promptinject`
                    attributes = plugins_config[namespace]
                    namespaced_klass = f"{namespace}.{classname}"
                    self._apply_config(attributes)
                    if classname in attributes:
                        self._apply_config(attributes[classname])
                    elif namespaced_klass in plugins_config:
                        logging.warning(
                            f"Deprecated configuration key found: {namespaced_klass}"
                        )
                        self._apply_config(plugins_config[namespaced_klass])
        self.loaded = True

    def _apply_config(self, config):
        classname = self.__class__.__name__
        for k, v in config.items():
            if k in _plugins.PLUGIN_TYPES or k == classname:
                # skip entries for more qualified items or any plugin type
                # should this be coupled to `_plugins`?
                continue
            if hasattr(self, "_supported_params") and k not in self._supported_params:
                # if the class has a set of supported params skip unknown params
                logging.warning(f"Unknown configuration key for {classname}: {k}")
                continue
            setattr(self, k, v)  # This will set attribute to the full dictionary value
