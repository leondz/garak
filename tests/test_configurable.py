from garak.configurable import Configurable
from garak._config import GarakSubConfig


class mockConfigurable(Configurable):
    # Configurable is coupled to hierarchy of plugin types
    __module__ = "garak.generators.mock"

    DEFAULT_PARAMS = {"class_var": "from_class"}

    def __init__(
        self,
        constructor_param=None,
        defaulted_constructor_param=None,
        config_root=GarakSubConfig(),
    ):
        self.constructor_param = constructor_param
        self.defaulted_constructor_param = defaulted_constructor_param
        self._load_config(config_root)


# when a parameter is provided in config_root set on the resulting object
def test_config_root_only():
    config = GarakSubConfig()
    generators = {
        "mock": {
            "constructor_param": "from_config",
            "defaulted_constructor_param": "from_config",
            "no_constructor_param": "from_config",
        }
    }
    setattr(config, "generators", generators)
    m = mockConfigurable(config_root=config)
    for k, v in generators["mock"].items():
        assert getattr(m, k) == v


# when a parameter is provided in config_root set on the resulting object
def test_config_root_as_dict():
    generators = {
        "mock": {
            "constructor_param": "from_config",
            "defaulted_constructor_param": "from_config",
            "no_constructor_param": "from_config",
        }
    }
    config = {"generators": generators}
    m = mockConfigurable(config_root=config)
    for k, v in generators["mock"].items():
        assert getattr(m, k) == v


# when a parameter is set in the same parameter name in the constructor will not be overridden by config
def test_param_provided():
    passed_param = "from_caller"
    config = GarakSubConfig()
    generators = {
        "mock": {
            "constructor_param": "from_config",
            "defaulted_constructor_param": "from_config",
            "no_constructor_param": "from_config",
        }
    }
    setattr(config, "generators", generators)
    m = mockConfigurable(passed_param, config_root=config)
    assert m.constructor_param == passed_param


# when a default parameter is provided and not config_root set on the resulting object
def test_class_vars_propagate_to_instance():
    config = GarakSubConfig()
    generators = {
        "mock": {
            "constructor_param": "from_config",
            "defaulted_constructor_param": "from_config",
            "no_constructor_param": "from_config",
        }
    }
    setattr(config, "generators", generators)
    m = mockConfigurable(config_root=config)
    assert m.class_var == m.DEFAULT_PARAMS["class_var"]


# when a default parameter is provided and not config_root set on the resulting object
def test_config_mask_class_vars_to_instance():
    config = GarakSubConfig()
    generators = {
        "mock": {
            "class_var": "from_config",
            "constructor_param": "from_config",
            "defaulted_constructor_param": "from_config",
            "no_constructor_param": "from_config",
        }
    }
    setattr(config, "generators", generators)
    m = mockConfigurable(config_root=config)
    assert m.class_var == "from_config"
