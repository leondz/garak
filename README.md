# garak, an llm vulnerability scanner

modular tool for probing LLMs for undesireable prompt responses

* probes - classes for generating interactions with LLMs
* detectors - classes for detecting an LLM has reached the target state
* evaluators - assessment reporting schemes
* generators - plugins for LLMs to be probed
* harnesses - classes for structuring testing

invoke with `python3 -m garak`

currently supports:
* [hugging face hub](https://huggingface.co/models) generative models
* [replicate](https://replicate.com/) text models
* [openai api](https://platform.openai.com/docs/introduction) continuation models

```
$ python3 -m garak --help
usage: garak.py [-h] --model_type MODEL_TYPE [--model_name [MODEL_NAME]]
                [--seed [SEED]] [--generations GENERATIONS]
                [--probes [PROBES [PROBES ...]]]
                [--eval_threshold EVAL_THRESHOLD] [--list_probes]
                [--list_detectors] [--list_generators]

LLM safety & security scanning tool

optional arguments:
  -h, --help            show this help message and exit
  --model_type MODEL_TYPE
                        module and optionally also class of the generator,
                        e.g. 'huggingface.HFBaseGenerator', or 'openai'
  --model_name [MODEL_NAME]
                        name of the model, e.g. 'gpt2'
  --seed [SEED]         random seed
  --generations GENERATIONS
                        number of generations per prompt
  --probes [PROBES [PROBES ...]]
                        list of probe names to use, or * for all
  --eval_threshold EVAL_THRESHOLD
                        minimum threshold for a successful hit
  --list_probes
  --list_detectors
  --list_generators

See https://github.com/leondz/garak
```

<hr>

_"Never tell the same lie twice"_ - Elim


CC-BY 2023 Leon Derczynski
