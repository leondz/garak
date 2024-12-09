Configuring ``garak``
=====================

Beyond the standard CLI options, garak is highly configurable.
You can use YAML files to configure a garak run, down to the level
of exactly how each plugin behaves.


Specifying custom configuration
-------------------------------

``garak`` can be configured in multiple ways:

* Via command-line parameters
* Using YAML configs
* Through specifying JSON on the command line

The easiest way is often to use a YAML config, and how to do that is 
described below.

Garak's config hierarchy
^^^^^^^^^^^^^^^^^^^^^^^^

Configuration values can come from multiple places. At garak load, the
``_config`` module manages parsing configuration. This includes determining
the priority of which values go where. The hierarchy is as follows:

1. Values given at the command line
2. Config values given in a YAML file passed via ``--config``
3. Values in a YAML site config, ``garak.site.yaml``, placed in the config directory (``XDG_CONFIG_DIR``, which is ``~/.config/garak/`` on Linux; see XDG spec for details)
4. Fixed values kept in the garak core config - don't edit this. Package updates will overwrite it, and you might break your garak install. It's in ``garak/resources`` if you want to take a look.
5. Default values specified in plugin code

Config YAML
^^^^^^^^^^^

Let's take a look at the core config.

.. code-block:: yaml

    ---
    system:
        verbose: 0
        narrow_output: false
        parallel_requests: false
        parallel_attempts: false
        lite: true
        show_z: false

    run:
        seed:
        deprefix: true
        eval_threshold: 0.5
        generations: 5
        probe_tags:

    plugins:
        model_type:
        model_name:
        probe_spec: all
        detector_spec: auto
        extended_detectors: false
        buff_spec:
        buffs_include_original_prompt: false
        buff_max: 
        detectors: {}
        generators: {}
        buffs: {}
        harnesses: {}
        probes:
            encoding:
                payloads:
                    - default

    reporting:
        report_prefix:
        taxonomy:
        report_dir: garak_runs
        show_100_pass_modules: true

    policy:
        threshold: false

Here we can see many entries that correspond to command line options, such as 
``model_name`` and ``model_type``, as well as some entried not exposed via CLI
such as ``show_100_pass_modules``.


``system`` config items
"""""""""""""""""""""""

* ``parallel_requests`` - For generators not supporting multiple responses per prompt: how many requests to send in parallel with the same prompt? (raising ``parallel_attempts`` generally yields higher performance, depending on how high ``generations`` is set)
* ``parallel_attempts`` - For parallelisable generators, how many attempts should be run in parallel? Raising this is a great way of speeding up garak runs for API-based models
* ``lite`` - Should we display a caution message that the run might not give very thorough results?
* ``verbose`` - Degree of verbosity (values above 0 are experimental, the report & log are authoritative)
* ``narrow_output`` - Support output on narrower CLIs
* ``show_z`` - Display Z-scores and visual indicators on CLI. It's good, but may be too much info until one has seen garak run a couple of times
* ``enable_experimental`` - Enable experimental function CLI flags. Disabled by default. Experimental functions may disrupt your installation and provide unusual/unstable results. Can only be set by editing core config, so a git checkout of garak is recommended for this.

``run`` config items
""""""""""""""""""""

* ``probe_tags`` - If given, the probe selection is filtered according to these tags; probes that don't match the tags are not selected
* ``generations`` - How many times to send each prompt for inference
* ``deprefix`` - Remove the prompt from the start of the output (some models return the prompt as part of their output)
* ``seed`` - An optional random seed
* ``eval_threshold`` - At what point in the 0..1 range output by detectors does a result count as a successful attack / hit
* ``policy_scan`` - Should the run include a scan to automatically determine the target's content policy?
* ``user_agent`` - What HTTP user agent string should garak use? ``{version}`` can be used to signify where garak version ID should go

``plugins`` config items
""""""""""""""""""""""""
* ``model_type`` - The generator model type, e.g. "nim" or "huggingface"
* ``model_name`` - The name of the model to be used (optional - if blank, type-specific default is used)
* ``probe_spec`` - A comma-separated list of probe modules or probe classnames (in ``module.classname``) format to be used. If a module is given, only ``active`` plugin in that module are chosen, this is equivalent to passing `-p` to the CLI
* ``detector_spec`` - An optional spec of detectors to be used, if overriding those recommended in probes. Specifying ``detector_spec`` means the ``pxd`` harness will be used. This is equivalent to passing `-d` to the CLI
* ``extended_detectors`` - Should just the primary detector be used per probe, or should the extended detectors also be run? The former is fast, the latter thorough.
* ``buff_spec`` - Comma-separated list of buffs and buff modules to use; same format as ``probe_spec``.
* ``buffs_include_original_prompt`` - When buffing, should the original pre-buff prompt still be included in those posed to the model?
* ``buff_max`` - Upper bound on how many items a buff should return
* ``detectors`` - Root node for detector plugin configs
* ``generators`` - Root note for generator plugin configs
* ``buffs`` - Root note for buff plugin configs
* ``harnesses`` - Root note for harness plugin configs
* ``probes`` - Root note for probe plugin configs

For an example of how to use the ``detectors``, ``generators``, ``buffs``, 
``harnesses``, and ``probes`` root entries, see `Configuring plugins with YAML <config_with_yaml>`_ below.

``reporting`` config items
""""""""""""""""""""""""""
* ``report_dir`` - Directory for reporting; defaults to ``$XDG_DATA/garak/garak_runs``
* ``report_prefix`` - Prefix for report files. Defaults to ``garak.$RUN_UUID``
* ``taxonomy`` - Which taxonomy to use to group probes when creating HTML report
* ``show_100_pass_modules`` - Should entries scoring 100% still be detailed in the HTML report?

``policy`` config items
"""""""""""""""""""""""
* ``threshold`` - pass rate for a behavior to be considered "permitted" when policy probed; false indicates any passes mean a positive, permissive policy


Bundled quick configs
^^^^^^^^^^^^^^^^^^^^^

Garak comes bundled with some quick configs that can be loaded directly using ``--config``.
These don't need the ``.yml`` extension when being requested. They include:

* ``broad`` - Run all active probes, just once each, for a rapid broad test
* ``fast`` - Go through a selection of light probes; skip extended detectors
* ``full`` - Select many probes, and multiple payloads; use a paraphrase buff to get multiple variations on each prompt
* ``long_attack_gen`` - Focus on ``atkgen``, with many generations, to give a higher chance of breaking through (i.e. yielding toxicity)
* ``notox`` - Scan without any toxicity-inducing probes
* ``tox_and_buffs`` - Go through toxicity & slur probes, using only relevant payloads, and a fast paraphraser

These are great places to look at to get an idea of how garak YAML configs can look.
Quick configs are stored under ``garak/configs/`` in the source code/install.


Using a custom config
^^^^^^^^^^^^^^^^^^^^^

To override values in this we can create a new YAML file and point to it from the 
command line using ``--config``. For example, to select just ``latentinjection``
probes and run each prompt just once:

.. code-block:: yaml
    
    ---
    run:
        generations: 1
    
    plugins:
        probe_spec: latentinjection

If we save this as ``latent1.yaml`` somewhere, then we can use it with ``garak --config latent1.yaml``.



Using a custom JSON config
^^^^^^^^^^^^^^^^^^^^^^^^^^

Some plugins can take a JSON config specified on the command line. This config 
has the same structure as a YAML config, starting with the plugin model/type.
The config can either be written to a file and the path passed, with 
`--generator_option_file` or `--probe_option_file`, or directly as JSON on the
command prompt, with `--generator_options` or `--probe_options`. An example 
is given in `RestGenerator Config with JSON <rest_generator_with_json>`_ below.


Configuring Plugins
-------------------

Garak's functions are through its plugins. Most parts of garak are plugins,
like the ``probes`` and ``detectors`` that do the actual examination of the target,
the ``generators`` that interface with models, and even the ``harnesses`` 
that manage run orchestration. Each plugin is a class that has both descriptive
and configurable parameters.

Viewing plugin parameters
^^^^^^^^^^^^^^^^^^^^^^^^^

You can see the parameters for any given plugin using garak ``--plugin_info``.

.. code-block:: text

    $ python -m garak --plugin_info probes.grandma.Win10
    garak LLM vulnerability scanner v0.10.0 ( https://github.com/NVIDIA/garak ) at 2024-09-11T11:54:07.215242
    Configured info on probes.grandma.Win10:
                            description: Will the model yield a Windows 10 product key if we beg it to?
                         DEFAULT_PARAMS: {'generations': 1}
                                 active: True
                                  bcp47: en
                                doc_uri: https://www.independent.co.uk/tech/chatgpt-microsoft-windows-11-grandma-exploit-b2360213.html
                     extended_detectors: ['mitigation.MitigationBypass']
                                   goal: get model to output Win 10 product keys
                               modality: {'in': ['text']}
                parallelisable_attempts: True
                       primary_detector: productkey.Win5x5
                                   tags: ['avid-effect:security:S0300', 'owasp:llm06', 'risk-cards:lmrc:providing_illegal_info', 'quality:Behavioral:ContentSafety:LegalGoodsServices']
                               mod_time: 2024-07-01 04:16:40 +0000

Here, we see a list of the descriptive parameters of the plugin. We can see
a link to documentation about it, which detectors it uses, tags describing
the probe in various typologies, which languages and modalities it supports, and more.

We can also see a ``DEFAULT_PARAMS`` entry. This is a dictionary containing
configurable parameters for this plugin. In this case, there's a ``generations``
parameter set to ``1``; this is the default value for ``probes``, but is often 
overridden at run time by the CLI setup.

At plugin load, the plugin instance has attributes named in ``DEFAULT_PARAMS``
automatically created, and populated with either values given in the supplied
config, or the default.

.. _config_with_yaml:

Configuring plugins with YAML
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Plugin config happens inside the ``plugins`` block. Multiple plugins can be 
configured in the same YAML. Descend through this specifying plugin type,
model, and optionally class, and set variables in the end. These will then
be loaded as the plugin's ``DEFAULT_PARAMS`` attribute is parsed and used to
populate instance attributes.

Here's an example of setting the temperature on an OpenAIGenerator:

.. code-block:: yaml

    plugins:
        generators:
            openai:
                OpenAIGenerator:
                    temperature: 1.0

As noted the class is optional, if the configuration defines keys at the module level
these will be applied to the instance and can be overridden by the class level. Here
is an example that is equivalent to the configuration above:

.. code-block:: yaml
    plugins:
        generators:
            openai:
                temperature: 1.0

Example: RestGenerator
^^^^^^^^^^^^^^^^^^^^^^

RestGenerator is a slightly complex generator, though mostly because it exposes
so many config values, allowing flexible integrations. This example sets 
``model_type: rest`` to ensure that this model is selected for the run; that might 
not always be wanted, and it isn't compulsory.

RestGenerator with YAML
"""""""""""""""""""""""

.. code-block:: yaml

    plugins:
        model_type: rest
        generators:
            rest:
                RestGenerator:
                    uri: https://api.example.ai/v1/
                    key_env_var: EXAMPLE_KEY
                    headers: Authentication: $KEY
                    response_json_field: text
                    request_timeout: 60

This defines a REST endpoint where:

* The URI is https://api.example.ai/v1/
* The API key can be found in the ``EXAMPLE_KEY`` environment variable's value (if unspecified, `REST_API_KEY` is checked)
* The HTTP header ``"Authentication:"`` should be sent in every request, with the API key as its parameter
* The output is JSON and the top-level field ``text`` holds the model's response
* Wait up to 60 seconds before timing out (the generator will backoff and retry when this is reached)

.. _rest_generator_with_json:

RestGenerator config with JSON
""""""""""""""""""""""""""""""

.. code-block:: JSON

    {
        "rest": {
            "RestGenerator": {
                "name": "example service",
                "uri": "https://127.0.0.1/llm",
                "method": "post",
                "headers": {
                    "X-Authorization": "$KEY"
                },
                "req_template_json_object": {
                    "text": "$INPUT"
                },
                "response_json": true,
                "response_json_field": "text"
            }
        }
    }

This defines a REST endpoint where:

* The URI is https://127.0.0.1/llm
* We'll use HTTP `POST` on requests
* The HTTP header ``"X-Authorization:"`` should be sent in every request, with the API key as its parameter
* The request template is to be a JSON dict with one key, `text`, holding the prompt
* The output is JSON and the top-level field ``text`` holds the model's response


This should be written to a file, and the file's path passed on the command 
line with `-G`. 

Configuration in code
---------------------

The preferred way to instantiate a plugin is using ``garak._plugins.load_plugin()``.
This function takes two parameters:

* ``name``, the plugin's package, module, and class - e.g. ``generator.test.Lipsum``
* (optional) ``config_root``, either garak._config or a dictionary of a config, beginning at a top-level plugin type.

``load_plugin()`` returns a configured instance of the requested plugin.

OpenAIGenerator config with dictionary
""""""""""""""""""""""""""""""""""""""

.. code-block:: python

    >>> import garak._plugins
    >>> c = {"generators":{"openai":{"OpenAIGenerator":{"seed":30,"name":"gpt-4"}}}}
    >>> garak._plugins.load_plugin("generators.openai.OpenAIGenerator", config_root=c)
    🦜 loading generator: OpenAI: gpt-4
    <garak.generators.openai.OpenAIGenerator object at 0x71bc97693d70>
