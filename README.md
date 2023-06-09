# garak, an llm vulnerability scanner

`garak` is a modular tool for probing LLMs for undesireable prompt responses

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

`garak` is a command-line tool. It's developed in Linux and OSX.

`garak` has its own dependencies. You'll probably want to install `garak` in its own Conda environment:

```
conda create --name garak
conda activate garak
gh repo clone leondz/garak
cd garak
pip3 install -r requirements.txt
```

OK, if that went fine, you're probably good to go!

## Getting started

The general syntax is:

`python3 -m garak <options>`

`garak` needs to know what model to scan, and by default, it'll try all the probes it knows on that model, using the vulnerability detectors recommended by each probe. You can see a list of probes using:

`python3 -m garak --list_probes`

To specify a generator, use the `--model_name` and, optionally, the `--model_type` options. Model name specifies a model family/interface; model type specifies the exact model to be used. The "Intro to generators" section below describes some of the generators supported. A straightfoward generator family is Hugging Face models; to load one of these, set `--model_name` to `huggingface` and `--model_type` to the model's name on Hub (e.g. `"RWKV/rwkv-4-169m-pile"`). Some generators might need an API key to be set as an environment variable, and they'll let you know if they need that.

`garak` runs all the probes by default, but you can be specific about that too. `--probes promptinject` will use only the [PromptInject](https://github.com/agencyenterprise/promptinject) framework's methods, for example. You can also specify one specific plugin instead of a plugin family by adding the plugin name after a `.`; for example, `--probes lmrc.Deadnaming` will use an implementation of checking for deadnaming based on the [Language Model Risk Cards](https://arxiv.org/abs/2303.18190) framework.

## Examples

Probe ChatGPT for encoding-based prompt injection (OSX/\*nix) (replace example value with a real OpenAI API key)
 
```
export OPENAI_API_KEY="sk-123XXXXXXXXXXXX"
python3 -m garak --model_type openai --model_name gpt-3.5-turbo --probes encoding
```

See if the Hugging Face version of GPT2 is vulnerable to DAN 11.0

```
python3 -m garak --model_type huggingface --model_name gpt2 --probes dan.Dan_11_0
```

Errors go in `garak.log`; the run is logged in detail in a `.jsonl` file specified at analysis start & end. Send PRs & open issues. Happy hunting!

## Intro to generators

### huggingface

* `--model_name huggingface` (for transformers models to run locally)
* `--model_type` - use the model name from Hub. Only generative models will work. If it fails and shouldn't, please open an issue and paste in the command you tried + the exception!

* `--model_name huggingface.InferenceAPI` (for API-based model access)
* `--model_type` - the model name from Hub, e.g. `"mosaicml/mpt-7b-instruct"`
* (optional) set the `HF_INFERENCE_TOKEN` environment variable to a Hugging Face API token with the "read" role; see https://huggingface.co/settings/tokens when logged in

### openai

* `--model_name openai`
* `--model_type` - the OpenAI model you'd like to use. `text-babbage-001` is fast and fine for testing; `gpt-4` seems weaker to many of the more subtle attacks.
* set the `OPENAI_API_KEY` environment variable to your OpenAI API key (e.g. "sk-19763ASDF87q6657"); see https://platform.openai.com/account/api-keys when logged in

Recognised model types are whitelisted, because the plugin needs to know which sub-API to use. Completion or ChatCompletion models are OK. If you'd like to use a model not supported, you should get an informative error message, and please send a PR / open an issue.

### replicate

* `--model_name replicate`
* `--model_type` - the Replicate model name and hash, e.g. `"stability-ai/stablelm-tuned-alpha-7b:c49dae36"`
* set the `REPLICATE_API_TOKEN` environment variable to your Replicate API token, e.g. "r8-123XXXXXXXXXXXX"; see https://replicate.com/account/api-tokens when logged in

### cohere

* `--model_name cohere`
* `--model_type` (optional, `command` by default) - The specific Cohere model you'd like to test
* set the `COHERE_API_KEY` environment variable to your Cohere API key, e.g. "aBcDeFgHiJ123456789"; see https://dashboard.cohere.ai/api-keys when logged in

### ggml

* `--model_name ggml`
* `--model_type` - The path to the ggml model you'd like to load, e.g. `/home/leon/llama.cpp/models/7B/ggml-model-q4_0.bin`
* set the `GGML_MAIN_PATH` environment variable to the path to your ggml `main` executable

### test

* `--model_name test`
* (alternatively) `--model_name test.Blank`
For testing. This always generates the empty string, using the `test.Blank` generator.  Will be marked as failing for any tests that *require* an output, e.g. those that make contentious claims and expect the model to refute them in order to pass.

* `--model_name test.Repeat`
For testing. This generator repeats back the prompt it received.

## Intro to probes

### blank
 
A simple probe that always sends an empty prompt.

### continuation

Probes that test if the model will continue a probably undesirable word

### dan

Various [DAN]() and DAN-like attacks

### encoding

Prompt injection through text encoding

### goodside

### knownbadsignatures

Probes that attempt to make the model output malicious content signatures

### lmrc

Subsample of the [Language Model Risk Cards](https://arxiv.org/abs/2303.18190) probes

### misleading

Attempts to make a model support misleading and false claims

### promptinject

Implementation of the Agency Enterprise [PromptInject](https://github.com/agencyenterprise/PromptInject/tree/main/promptinject) work (best paper awards @ NeurIPS ML Safety Workshop 2022)

### realtoxicityprompts

Subset of the RealToxicityPrompts work (data constrained because the full test will take so long to run)

### snowball

[Snowballed Hallucination](https://ofir.io/snowballed_hallucination.pdf) probes designed to make a model give a wrong answer to questions too complex for it to process

### art

Auto Red-Team. A red-teaming LLM probes the target and reacts to it in an attempt to get toxic output. Prototype, mostly stateless, for now uses a simple GPT-2 [fine-tuned](https://huggingface.co/leondz/artgpt2tox) on the subset of hhrlhf attempts that yielded detectable toxicity (the only target currently supported for now).

## Logging

`garak` generates two kinds of log:
* A log file, `garak.log`. This includes debugging information from `garak` and its plugins, and is continued across runs.
* A report of the current run, structured as JSONL. A new report file is created every time `garak` runs. The name of this file is output at the beginning and, if successful, also the end of the run. In the report, an entry is made for each probing attempt both as the generations are received, and again when they are evaluated; the entry's `status` attribute takes a constant from `garak.attempts` to describe what stage it was made at.

## How is the code structured?

In a typical run, `garak` will read a model type (and optionally model name) from the command line, then determine which `probe`s and `detector`s to run, start up a `generator`, and then pass these to a `harness` to do the probing; an `evaluator` deals with the results. There are many modules in each of these categories, and each module provides a number of classes that act as individual plugins.

* `garak/probes/` - classes for generating interactions with LLMs
* `garak/detectors/` - classes for detecting an LLM is exhibiting a given failure mode
* `garak/evaluators/` - assessment reporting schemes
* `garak/generators/` - plugins for LLMs to be probed
* `garak/harnesses/` - classes for structuring testing
* `resources/` - ancillary items required by plugins

The default operating mode is to use the `probewise` harness. Given a list of probe module names and probe plugin names, the `probewise` harness instantiates each probe, then for each probe reads its `recommended_detectors` attribute to get a list of `detector`s to run on the output.

Each plugin category (`probes`, `detectors`, `evaluators`, `generators`, `harnesses`) includes a `base.py` which defines the base classes usable by plugins in that category. Each plugin module defines plugin classes that inherit from one of the base classes. For example, `garak.generators.openai.OpenAIGenerator` descends from `garak.generators.base.Generator`.

Larger artefacts, like model files and bigger corpora, are kept out of the repository; they can be stored on e.g. Hugging Face Hub and loaded locally by clients using `garak`.


## Developing your own plugin

* Take a look at how other plugins do it
* Inherit from one of the base classes, e.g. `garak.probes.base.TextProbe`
* Override as little as possible
* You can test the new code in at least two ways:
  * Start an interactive Python session
    * Import the model, e.g. `import garak.probes.mymodule`
    * Instantiate the plugin, e.g. `p = garak.probes.mymodule.MyProbe()`
  * Run a scan with test plugins
    * For probes, try a blank generator and always.Pass detector: `python3 -m garak -m test.Blank -p mymodule -d always.Pass`
    * For detectors, try a blank generator and a blank probe: `python3 -m garak -m test.Blank -p blank -d mymodule`
    * For generators, try a blank probe and always.Pass detector: `python3 -m garak -m mymodule -p blank -d always.Pass`
  * Get `garak` to list all the plugins of the type you're writing, with `--list_probes`, `--list_detectors`, or `--list_generators`

Reach out if you have any questions!

<hr>

_"Never tell the same lie twice"_ - Elim


© GPLv3 2023 Leon Derczynski
