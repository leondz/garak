Welcome to the garak documentation
==================================

**garak** is an LLM vulnerability scanner.
It uses a huge range of probes to examine and query a large language model, simulating
attacks, and uses a range of detectors on the model's outputs to see if the model was 
vulnerable to any of those attacks.

This is the code reference documentation, mostly useful for developers and people interested
in how garak works. There is a separate `user guide <https://docs.garak.ai>`_ containing information
on running garak and interpreting results. If you just want to use the tool and don't care about
it's internals, you want the user guide. If you'd like a tour of the details or to contribute
code, you're in the right place - welcome!

You can also join our `Discord <https://discord.gg/xH3rs3ZH4B>`_
and follow us on `Twitter <https://twitter.com/garak_llm>`_!

Check out the :doc:`usage` section for further information, including
how to :ref:`installation` the project.

.. note::

   This project is under active development.

Contents
--------

.. toctree::

   usage
   contributing
   basic
   probes
   detectors
   generators
   harnesses
   evaluators
