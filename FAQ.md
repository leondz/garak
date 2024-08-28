# garak LLM probe: Frequently Asked Questions


## How do I pronounce garak?

Good question! Emphasis on the first bit, GA-rak. 

Both 'a's like a in English "hat", or à in French, or /æ/ in IPA.

## What's this tool for?

`garak` is designed to help discover situations where a language model generates outputs that one might not want it to. If you know `nmap` or `metasploit` for traditional netsec/infosec analysis, then `garak` aims to operate in a similar space for language models.

## How does garak work?

`garak` has probes that try to look for different "vulnerabilities". Each probs sends specific prompts to models, and gets multiple generations for each prompt. LLM output is often stochastic, so a single test isn't very informative. These generations are then processed by "detectors", which will look for "hits". If a detector registers a hit, that attempt is registered as failing. Finally, a report is output with the success/failure rate for each probe and detector.

## Do these results have scientific validity?

No. The scores from any probe don't operate on any kind of normalised scale. Higher passing percentage is better, but that's it. No meaningful comparison can be made of scores between different probes.

## How does it determine a pass/fail score for replies?

Each detector is different. Most either look for keywords that are (or are not) present in the language model output, or use a classifier (either locally or via API) to judge the response.

## Does garak allow for additional prompts ?

Additional prompts can be probed by creating a new plugin -- this isn't as tough as it sounds; take a look at the modules in the `garak/probes/` directory for inspiration.

## How will a auditor know what was used in testing?

The JSONL report created for each run includes language model parameters, all the prompts sent to the mode, all the model responses, and also the mapping between these and evaluation scores. There's a JSONL report analysis script in `analyse/analyse_log.py`.

## Do you have plans to setup an environment for running these tests on HuggingFace?

Not immediately, but if you have the Gradio skills, get in touch!

## Can you add support for vulnerability X?

Perhaps - please [open an issue](https://github.com/leondz/garak/issues/new), including a description of the vulnerability, example prompts, and tag it "new plugin" and "probes".

## Can you add support for model X?

Would love to! Please [open an issue](https://github.com/leondz/garak/issues/new), tagging it "new plugin" and "generators".

## How much disk space do I need to run garak?

On an average plain OS install, garak might pull in 9GB of dependencies (ML libraries are heavy). If you're running a model locally, enough space will be required for that model plus its dependencies, too - check out the model's files for an estimate.  Hugging Face gpt2 is about 5GB (https://huggingface.co/google/gemma-2-2b-it/tree/main), whereas Hugging Face Llama-3.1-405B is around half a terabyte (https://huggingface.co/meta-llama/Meta-Llama-3.1-405B/tree/main). Garak sometimes uses machine learning-based detectors, but we go for smaller variants, so I'd guess/hope under 2GB. Finally, logs generated while running can be up to 60MB per standard run - ymmv!

Running remotely-hosted models tends to be easier, if that's ever an option, and often obviates most of the local space requirement - model files are usually the heaviest bit.

## Are there instructions for Hugging Face gated models?

Gated models simply require login and in some case acceptance of model provider license terms. [Here](https://huggingface.co/docs/huggingface_hub/en/guides/cli) are details of huggingface-cli login process.

## Is it safe to build garak into toolchains? Who's supporting this?

NVIDIA Corporation officially contributes to the garak open-source project and will continue to do so in the long term. Garak will continue to be licensed with Apache 2.0. Get in touch if you'd like to talk more about this.

## Can an LLM have vulnerabilities?

The things garak probes for are generally not like traditional cybersec vulnerabilities. LLM model parameters don't and can't have vulnerabilities themselves; it's just data. What most of the probes in garak check for are whether or not a model can be made to behave unexpectedly at inference time, by breaking its alignment or output policy, using exploits. The DHS calls some of these behaviours "weaknesses"; see e.g. [CWE-1426](https://cwe.mitre.org/data/definitions/1426.html) for prompt injection. 

Some garak probes still check for traditional cybersecurity vulnerabilities within the scope of what can be extracted from APIs also used for inference.

## I tried to scan a model from HuggingFace, but for some reason, the process got killed when loading checkpoint shards. I ran the scan in my Jupyter notebook locally, the model had already been downloaded during a previous run. I couldn't get past 75% without the process being killed. 

This sounds like hitting a resource limit - something external to garak, e.g. the kernel, has taken action. Does your process have access to the required system RAM and GPU memory

## How can I use garak to scan a NIM of an LLM?  What should the "model_type" be? And how do we pass the NIM endpoint url to garak?

`model_type` should be "nim" for chat-type models (which is most of them - this selects the right class automatically. Then, set model_name to [organisation]/[model name] from [build.nvidia.com](https://build.nvidia.com) (the JSON example is authoritative). For example, `--model_type nim --model_name meta/llama-3.1-8b-instruct`. You will need to put the API key in the `NIM_API_KEY` environment variable, or in the config.

## If I have already scanned a model on HuggingFace, and I use the same model somewhere else, say in a container, is it necessary for me to scan the container with garak as well?

No, if the model is the same, you should get the same results - though there are some probes that scan the model files themself, which work on Hugging Face but not via a container.

## How can I scan a RAG pipeline with garak?

Currently the major attack we hear about in RAG systems is indirect prompt injection, and garak already scans for a few of those.

## There are so many probes in garak, I was trying to scan a model for all probes, but it took hours and I eventually had to kill that scan. What is the recommended practice on scanning a model? Which typical probes are recommended?

Recommended practice: it's really context dependent. The builtin "fast" config works pretty well (`--config fast`). It's also useful to run with `--parallel_attempts` (using a value of e.g. 20 or 40) if the model isn't local.

## Once a model is scanned, there is really no need to scan it again for the same probe(s) unless the model has been customized/finetuned?

We update garak by improving existing probes or adding new ones quite frequently, and so scores will go down over time - garak isn't a benchmark, and the more we learn about failures in LLMs, the harder garak gets. But if you're looking at a short period of just a month or two, then the scores will probably stay pretty much the same. We do not recommend relying on scores over six months old.




<!-- ## Why the name?

It's named after a smooth-talking, manipulative, persuasive, well-written character from a nineties TV series. Because we need tools like that to dissect LLM behavior. -->
