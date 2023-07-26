CLI reference for garak
=======================

::

  garak LLM security probe v0.9.0.7 ( https://github.com/leondz/garak ) at 2023-07-26T09:42:45.231512
  usage: __main__.py [-h] [--model_type MODEL_TYPE] [--model_name MODEL_NAME]
                     [--seed SEED] [--generations GENERATIONS] [--probes PROBES]
                     [--detectors DETECTORS] [--eval_threshold EVAL_THRESHOLD]
                     [--deprefix] [--plugin_info PLUGIN_INFO] [--list_probes]
                     [--list_detectors] [--list_generators] [--version]
                     [--verbose] [--generator_option GENERATOR_OPTION]
                     [--probe_options PROBE_OPTIONS]
                     [--report_prefix REPORT_PREFIX] [--narrow_output]
                     [--report REPORT] [--extended_detectors]
  
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
    --eval_threshold EVAL_THRESHOLD
                          minimum threshold for a successful hit
    --deprefix            remove the prompt from the front of system output
    --plugin_info PLUGIN_INFO
                          show info about one plugin; format as
                          type.plugin.class, e.g. probes.lmrc.Profanity
    --list_probes         list available vulnerability probes
    --list_detectors      list available detectors
    --list_generators     list available generation model interfaces
    --version, -V         print version info & exit
    --verbose, -v         add one or more times to increase verbosity of output
                          during runtime
    --generator_option GENERATOR_OPTION, -G GENERATOR_OPTION
                          options to pass to the generator
    --probe_options PROBE_OPTIONS, -P PROBE_OPTIONS
                          options to pass to probes, formatted as a JSON dict
    --report_prefix REPORT_PREFIX
                          Specify an optional prefix for the report and hit logs
    --narrow_output       give narrow CLI output
    --report REPORT, -r REPORT
                          process garak report into a list of AVID reports
    --extended_detectors  If detectors aren't specified on the command line,
                          should we run all detectors? (default is just the
                          primary detector, if given, else everything)
  
  See https://github.com/leondz/garak
