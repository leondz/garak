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
* [openai api](https://platform.openai.com/docs/introduction) chat & continuation models
* ggml models like [llama.cpp](https://github.com/ggerganov/llama.cpp)

```
$ python3 -m garak --help
garak LLM probe v0.9 ( https://github.com/leondz/garak ) at 2023-05-30T12:36:42.155472
usage: __main__.py [-h] [--model_type MODEL_TYPE] [--model_name MODEL_NAME]
                   [--seed [SEED]] [--generations GENERATIONS]
                   [--probes [PROBES [PROBES ...]]]
                   [--eval_threshold EVAL_THRESHOLD] [--list_probes]
                   [--list_detectors] [--list_generators] [--version] [-v]

LLM safety & security scanning tool

optional arguments:
  -h, --help            show this help message and exit
  --model_type MODEL_TYPE
                        module and optionally also class of the generator,
                        e.g. 'huggingface', or 'openai'
  --model_name MODEL_NAME
                        name of the model, e.g.
                        'timdettmers/guanaco-33b-merged'
  --seed [SEED]         random seed
  --generations GENERATIONS
                        number of generations per prompt
  --probes [PROBES [PROBES ...]]
                        list of probe names to use, or * for all (default)
  --eval_threshold EVAL_THRESHOLD
                        minimum threshold for a successful hit
  --list_probes
  --list_detectors
  --list_generators
  --version
  -v, --verbose

See https://github.com/leondz/garak
```




## Install:

Basic:
```
gh repo clone leondz/garak
cd garak
pip3 install -r requirements.txt
```

Install garak in its own Conda environment:

```
conda create --name garak
conda activate garak
gh repo clone leondz/garak
cd garak
pip3 install -r requirements.txt
```
## Examples

Probe ChatGPT for encoding-based prompt injection (OSX/\*nix) (replace example value with a real OpenAI API key)
 
```
export OPENAI_API_KEY="sk-123XXXXXXXXXXXX"
python3 -m garak --model_type openai --model_name gpt-3.5-turbo --probes encoding
```

Errors go in `garak.log`; the run is logged in detail in a `.jsonl` file specified at analysis start & end. Send PRs & open issues. Happy hunting!


<hr>

_"Never tell the same lie twice"_ - Elim


© GPLv3 2023 Leon Derczynski
