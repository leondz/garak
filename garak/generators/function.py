"""function-based generator

Call a given function to use as a generator; specify this as either the 
model name on the command line, or as the parameter to the constructor.

This generator is designed to be used programmatically, rather than 
invoked from the CLI. An example usage might be:

```
import mymodule
import garak.generators.function

g = garak.generators.function.Single(name="mymodule#myfunction")
```

The target function is expected to take a string, and return a string.
Other arguments passed by garak are forwarded to the target function.

Note that one can import the intended target module into scope and then
invoke a garak run via garak's cli module, using something like:

```
import garak
import garak.cli
import mymodule

garak.cli.main("--model_type function --model_name mymodule#function_name --probes encoding.InjectBase32".split())
```

"""

import importlib
from typing import List, Union

from garak import _config
from garak.generators.base import Generator


class Single(Generator):
    """pass a module#function to be called as generator, with format function(prompt:str, **kwargs)->List[Union(str, None)] the parameter name `generations` is reserved"""

    DEFAULT_GENERATIONS = 10
    uri = "https://github.com/leondz/garak/issues/137"
    generator_family_name = "function"
    supports_multiple_generations = False

    def __init__(
        self, name="", generations=DEFAULT_GENERATIONS, config_root=_config, **kwargs
    ):  # name="", generations=self.generations):
        context = config_root.plugins.generators
        self.kwargs = kwargs.copy()
        self.generations = generations  # if the user's function requires `generations` it would have been extracted from kwargs and will not be passed later

        if name:
            gen_args = {"name": name}
            json_config_format = {self.__module__: {self.__class__.__name__: gen_args}}
            _config._combine_into(json_config_format, context)

        self._load_config(context)

        gen_module_name, gen_function_name = self.name.split("#")

        gen_module = importlib.import_module(
            gen_module_name
        )  # limits ability to test this for general instantiation
        self.generator = getattr(gen_module, gen_function_name)
        # for name, klass in inspect.getmembers(base_klass, inspect.isclass)
        import inspect

        if "generations" in inspect.signature(self.generator).parameters:
            raise ValueError(
                'Incompatible function signature: "generations" is incompatible with this Generator'
            )

        super().__init__(name, generations=self.generations, config_root=config_root)

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        return self.generator(prompt, **self.kwargs)


class Multiple(Single):
    """pass a module#function to be called as generator, with format function(prompt:str, generations:int, **kwargs)->List[Union(str, None)]"""

    supports_multiple_generations = True

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        return self.generator(prompt, generations=generations_this_call, **self.kwargs)


DEFAULT_CLASS = "Single"
