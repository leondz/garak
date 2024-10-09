The `translator.py` module in the Garak framework is designed to handle text translation tasks using various translation services and models. 
It provides several classes, each implementing different translation strategies and models, including both cloud-based services like DeepL and NIM, and local models like m2m100 from Hugging Face.

garak.translator
=============

.. automodule:: garak.translator
   :members:
   :undoc-members:
   :show-inheritance:   

Multilingual support
====================

This feature adds multilingual probes and detector keywords and triggers.
You can check the model vulnerability for multilingual languages.

* limitation:
  - This function only supports for `bcp47` code is "en".
  - Huggingface detector only supports English. You need to bring the target language NLI model for the detector.
  - Some detectors only support English, such as the `snowball` detector.
  - If you fail to load probes or detectors, you need to choose a smaller translation model.

pre-requirements
----------------

.. code-block:: bash

    pip install nvidia-riva-client==2.16.0  pyenchant==3.2.2

Support translation service
---------------------------

- Huggingface
  - This code uses the following translation models:
    - `Helsinki-NLP/opus-mt-en-{lang} <https://huggingface.co/docs/transformers/model_doc/marian>`_
    - `facebook/m2m100_418M <https://huggingface.co/facebook/m2m100_418M>`_
    - `facebook/m2m100_1.2B <https://huggingface.co/facebook/m2m100_1.2B>`_
- `DeepL <https://www.deepl.com/docs-api>`_
- `NIM <https://build.nvidia.com/nvidia/megatron-1b-nmt>`_

API KEY
-------

You can use DeepL API or NIM API to translate probe and detector keywords and triggers.

You need an API key for the preferred service.
- `DeepL <https://www.deepl.com/en/pro-api>`_
- `NIM <https://build.nvidia.com/nvidia/megatron-1b-nmt>`_

Supported languages:
- `DeepL <https://developers.deepl.com/docs/resources/supported-languages>`_
- `NIM <https://build.nvidia.com/nvidia/megatron-1b-nmt/modelcard>`_

Set up the API key with the following command:

DeepL
~~~~~

.. code-block:: bash

    export DEEPL_API_KEY=xxxx

NIM
~~~

.. code-block:: bash

    export NIM_API_KEY=xxxx

config file
-----------

You can pass the translation service, source language, and target language by the argument.

- translation_service: "nim" or "deepl", "local"
- lang_spec: "ja", "ja,fr" etc. (you can set multiple language codes)

* Note: The `Helsinki-NLP/opus-mt-en-{lang}` case uses different language formats. The language codes used to name models are inconsistent. Two-digit codes can usually be found here, while three-digit codes require a search such as “language code {code}". More details can be found `here <https://github.com/Helsinki-NLP/OPUS-MT-train/tree/master/models>`_.

You can also configure this via a config file:

.. code-block:: yaml

    run:
      translation_service: {you choose translation service "nim" or "deepl", "local"}
      lang_spec: {you choose language code}

Examples for multilingual
-------------------------

DeepL
~~~~~

To use the translation option for garak, run the following command:

.. code-block:: bash

    export DEEPL_API_KEY=xxxx
    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --translation_service deepl --lang_spec ja

If you save the config file as "garak/configs/simple_translate_config_deepl.yaml", use this command:

.. code-block:: bash

    export DEEPL_API_KEY=xxxx
    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --config garak/configs/simple_translate_config_deepl.yaml

Example config file:

.. code-block:: yaml

    run:
      translation_service: "deepl"
      lang_spec: "ja"

NIM
~~~

For NIM, run the following command:

.. code-block:: bash

    export NIM_API_KEY=xxxx
    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --translation_service nim --lang_spec ja

If you save the config file as "garak/configs/simple_translate_config_nim.yaml", use this command:

.. code-block:: bash

    export NIM_API_KEY=xxxx
    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --config garak/configs/simple_translate_config_nim.yaml

Example config file:

.. code-block:: yaml

    run:
      translation_service: "nim"
      lang_spec: "ja"

Local
~~~~~

For local translation, use the following command:

.. code-block:: bash

    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --translation_service local --lang_spec ja

If you save the config file as "garak/configs/simple_translate_config_local.yaml", use this command:

.. code-block:: bash

    python3 -m garak --model_type nim --model_name meta/llama-3.1-8b-instruct --probes encoding --config garak/configs/simple_translate_config_local.yaml

Example config file:

.. code-block:: yaml

    run:
      translation_service: local
      local_model_name: "facebook/m2m100_418M"
      local_tokenizer_name: "facebook/m2m100_418M"
      lang_spec: "ja"
