CLI reference for garak
=======================

::

  garak LLM vulnerability scanner v0.9.0.14 ( https://github.com/leondz/garak ) at 2024-07-29T15:04:47.649692
  usage: python -m garak [-h] [--verbose] [--report_prefix REPORT_PREFIX]
                         [--narrow_output]
                         [--parallel_requests PARALLEL_REQUESTS]
                         [--parallel_attempts PARALLEL_ATTEMPTS]
                         [--skip_unknown] [--seed SEED] [--deprefix]
                         [--eval_threshold EVAL_THRESHOLD]
                         [--generations GENERATIONS] [--config CONFIG]
                         [--model_type MODEL_TYPE] [--model_name MODEL_NAME]
                         [--generator_option_file GENERATOR_OPTION_FILE | --generator_options GENERATOR_OPTIONS]
                         [--probes PROBES]
                         [--probe_option_file PROBE_OPTION_FILE | --probe_options PROBE_OPTIONS | --probe_tags PROBE_TAGS]
                         [--detectors DETECTORS] [--extended_detectors]
                         [--buffs BUFFS] [--taxonomy TAXONOMY]
                         [--plugin_info PLUGIN_INFO] [--list_probes]
                         [--list_detectors] [--list_generators] [--list_buffs]
                         [--list_config] [--version] [--report REPORT]
                         [--interactive] [--generate_autodan] [--interactive.py]
  
  LLM safety & security scanning tool
  
  options:
    -h, --help            show this help message and exit
    --verbose, -v         add one or more times to increase verbosity of output
                          during runtime
    --report_prefix REPORT_PREFIX
                          Specify an optional prefix for the report and hit logs
    --narrow_output       give narrow CLI output
    --parallel_requests PARALLEL_REQUESTS
                          How many generator requests to launch in parallel for
                          a given prompt. Ignored for models that support
                          multiple generations per call.
    --parallel_attempts PARALLEL_ATTEMPTS
                          How many probe attempts to launch in parallel.
    --skip_unknown        allow skip of unknown probes, detectors, or buffs
    --seed SEED, -s SEED  random seed
    --deprefix            remove the prompt from the front of generator output
    --eval_threshold EVAL_THRESHOLD
                          minimum threshold for a successful hit
    --generations GENERATIONS, -g GENERATIONS
                          number of generations per prompt
    --config CONFIG       YAML config file for this run
    --model_type MODEL_TYPE, -m MODEL_TYPE
                          module and optionally also class of the generator,
                          e.g. 'huggingface', or 'openai'
    --model_name MODEL_NAME, -n MODEL_NAME
                          name of the model, e.g.
                          'timdettmers/guanaco-33b-merged'
    --generator_option_file GENERATOR_OPTION_FILE, -G GENERATOR_OPTION_FILE
                          path to JSON file containing options to pass to
                          generator
    --generator_options GENERATOR_OPTIONS
                          options to pass to the generator
    --probes PROBES, -p PROBES
                          list of probe names to use, or 'all' for all
                          (default).
    --probe_option_file PROBE_OPTION_FILE, -P PROBE_OPTION_FILE
                          path to JSON file containing options to pass to probes
    --probe_options PROBE_OPTIONS
                          options to pass to probes, formatted as a JSON dict
    --probe_tags PROBE_TAGS
                          only include probes with a tag that starts with this
                          value (e.g. owasp:llm01)
    --detectors DETECTORS, -d DETECTORS
                          list of detectors to use, or 'all' for all. Default is
                          to use the probe's suggestion.
    --extended_detectors  If detectors aren't specified on the command line,
                          should we run all detectors? (default is just the
                          primary detector, if given, else everything)
    --buffs BUFFS, -b BUFFS
                          list of buffs to use. Default is none
    --taxonomy TAXONOMY   specify a MISP top-level taxonomy to be used for
                          grouping probes in reporting. e.g. 'avid-effect',
                          'owasp'
    --plugin_info PLUGIN_INFO
                          show info about one plugin; format as
                          type.plugin.class, e.g. probes.lmrc.Profanity
    --list_probes         list available vulnerability probes
    --list_detectors      list available detectors
    --list_generators     list available generation model interfaces
    --list_buffs          list available buffs/fuzzes
    --list_config         print active config info (and don't scan)
    --version, -V         print version info & exit
    --report REPORT, -r REPORT
                          process garak report into a list of AVID reports
    --interactive, -I     Enter interactive probing mode
    --generate_autodan    generate AutoDAN prompts; requires --prompt_options
                          with JSON containing a prompt and target
    --interactive.py      Launch garak in interactive.py mode
  
  See https://github.com/leondz/garak
