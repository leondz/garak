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

from garak.generators.base import Generator


class Single(Generator):
    """pass a module#function to be called as generator, with format function(prompt:str, **kwargs)->str"""

    uri = "https://github.com/leondz/garak/issues/137"
    generator_family_name = "function"
    supports_multiple_generations = False

    def __init__(self, name="", **kwargs):  # name="", generations=self.generations):
        gen_module_name, gen_function_name = name.split("#")
        if "generations" in kwargs:
            self.generations = kwargs["generations"]
            del kwargs["generations"]

        self.kwargs = kwargs

        gen_module = importlib.import_module(gen_module_name)
        self.generator = getattr(gen_module, gen_function_name)

        super().__init__(name, generations=self.generations)

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> Union[List[str], str, None]:
        return self.generator(
            prompt, generations_this_call=generations_this_call, **self.kwargs
        )


class Multiple(Single):
    """pass a module#function to be called as generator, with format function(prompt:str, generations:int, **kwargs)->List[str]"""

    supports_multiple_generations = True

    def _call_model(
        self, prompt: str, generations_this_call: int = 1
    ) -> Union[List[str], str, None]:
        return self.generator(prompt, generations=generations_this_call, **self.kwargs)


default_class = "Single"
