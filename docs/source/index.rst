Welcome to the garak reference documentation
============================================

**garak** is an LLM vulnerability scanner, `<https://garak.ai>`_.
It uses a huge range of probes to examine and query a large language model, simulating
attacks, and uses a range of detectors on the model's outputs to see if the model was 
vulnerable to any of those attacks.

This is the code reference documentation, mostly useful for developers and people interested
in how garak works. There is a separate `User Guide <https://docs.garak.ai>`_ containing information
on running garak and interpreting results. If you want to use the tool and get results,
and you don't care about its internals, then you want the user guide. Take a look there! `<https://docs.garak.ai>`_

On the other hand, if you'd like a to get into the the details or work out how 
to contribute code, you're in the right place - welcome!

You can also join our `Discord <https://discord.gg/uVch4puUCs>`_
and follow us on `Twitter <https://twitter.com/garak_llm>`_!

Check out the :doc:`usage` section for further information, including :ref:`installation`.

.. note::

   This project is under active development. We love writing and fixing docs, so
   let us know if there's anything wrong, confusing, or missing here --
   mail `docs@garak.ai <mailto:docs@garak.ai>`_ or drop us a note on `Discord <https://discord.gg/uVch4puUCs>`_. 
   Thank you!

Contents
--------


Using garak
^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   how
   usage
   reporting

Advanced usage
^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   configurable
   cliref

Code reference
^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   contributing

   basic
   attempt
   cli
   command
   exception
   interactive
   payloads
   _config
   _plugins
   translator

Plugin structure
^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   buffs
   detectors
   evaluators
   generators
   harnesses
   probes
   report
