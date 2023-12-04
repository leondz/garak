CLI reference for garak
=======================

::

  garak LLM security probe v0.9.0.8 ( https://github.com/leondz/garak ) at 2023-11-14T17:00:32.654683
  usage: __main__.py [-h] [--model_type MODEL_TYPE] [--model_name MODEL_NAME]
                     [--seed SEED] [--generations GENERATIONS] [--probes PROBES]
                     [--detectors DETECTORS] [--buff BUFF]
                     [--eval_threshold EVAL_THRESHOLD] [--deprefix]
                     [--plugin_info PLUGIN_INFO] [--list_probes]
                     [--list_detectors] [--list_generators] [--list_buffs]
                     [--version] [--verbose]
                     [--generator_option_file GENERATOR_OPTION_FILE | --generator_options GENERATOR_OPTIONS]
                     [--probe_option_file PROBE_OPTION_FILE | --probe_options PROBE_OPTIONS]
                     [--report_prefix REPORT_PREFIX] [--narrow_output]
                     [--report REPORT] [--extended_detectors] [--interactive]
                     [--parallel_requests PARALLEL_REQUESTS]
                     [--parallel_attempts PARALLEL_ATTEMPTS]
                     [--generate_autodan]
  
  LLM safety & security scanning tool
  
  options:
    -h, --help            show this help message and exit
    --model_type MODEL_TYPE, -m MODEL_TYPE
                          module and optionally also class of the generator,
                          e.g. 'huggingface', or 'openai'
    --model_name MODEL_NAME, -n MODEL_NAME
                          name of the model, e.g.
                          'timdettmers/guanaco-33b-merged'
    --seed SEED, -s SEED  random seed
    --generations GENERATIONS, -g GENERATIONS
                          number of generations per prompt
    --probes PROBES, -p PROBES
                          list of probe names to use, or 'all' for all
                          (default).
    --detectors DETECTORS, -d DETECTORS
                          list of detectors to use, or 'all' for all. Default is
                          to use the probe's suggestion.
    --buff BUFF, -b BUFF  buff to use
    --eval_threshold EVAL_THRESHOLD
                          minimum threshold for a successful hit
    --deprefix            remove the prompt from the front of system output
    --plugin_info PLUGIN_INFO
                          show info about one plugin; format as
                          type.plugin.class, e.g. probes.lmrc.Profanity
    --list_probes         list available vulnerability probes
    --list_detectors      list available detectors
    --list_generators     list available generation model interfaces
    --list_buffs          list available buffs/fuzzes
    --version, -V         print version info & exit
    --verbose, -v         add one or more times to increase verbosity of output
                          during runtime
    --generator_option_file GENERATOR_OPTION_FILE, -G GENERATOR_OPTION_FILE
                          path to JSON file containing options to pass to
                          generator
    --generator_options GENERATOR_OPTIONS
                          options to pass to the generator
    --probe_option_file PROBE_OPTION_FILE, -P PROBE_OPTION_FILE
                          path to JSON file containing options to pass to probes
    --probe_options PROBE_OPTIONS
                          options to pass to probes, formatted as a JSON dict
    --report_prefix REPORT_PREFIX
                          Specify an optional prefix for the report and hit logs
    --narrow_output       give narrow CLI output
    --report REPORT, -r REPORT
                          process garak report into a list of AVID reports
    --extended_detectors  If detectors aren't specified on the command line,
                          should we run all detectors? (default is just the
                          primary detector, if given, else everything)
    --interactive, -I     Enter interactive probing mode
    --parallel_requests PARALLEL_REQUESTS
                          How many generator requests to launch in parallel for
                          a given prompt. Ignored for models that support
                          multiple generations per call.
    --parallel_attempts PARALLEL_ATTEMPTS
                          How many probe attempts to launch in parallel.
    --generate_autodan    generate AutoDAN prompts; requires --prompt_options
                          with JSON containing a prompt and target
  
  See https://github.com/leondz/garak
