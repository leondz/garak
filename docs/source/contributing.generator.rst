Let's build a generator!
========================

Let's build a garak generator. In garak, generators provide abstraction between the main code base and a dialogue system. That system is often an LLM, but can be anything that accepts and returns text (or text plus some other modality).

In this example, we're going to build a module for interfacing with the LLMs hosted by `Replicate <https://replicate.com/>`_, using the Replicate API (`docs <https://replicate.com/docs/get-started/python>`_). We'll assume that we're working in a file called ``replicate.py``.

Inheritance
===========

All generators in garak must descend from ``garak.generators.base.Generator``. So, new generators start out like:

.. code-block:: python

    from garak.generators.base import Generator

    class ReplicateGenerator(Generator):
        """
        Interface for public endpoints of models hosted in Replicate (replicate.com).
        """
        pass

Class docstrings are mandatory in garak, enforced by a test that's required to pass before merging. And they're just sensible practice anyway. So we add a brief docstring here too.

It's important that generators always inheirt from ``garak.generators.base.Generator``. Not only does this often save a lot of work - using the logic in base's ``generate()`` is helpful - plugin listing also checks the parents of each class in each plugin when choosing to show a plugin as available. If there's a class in a module in ``garak/generators/`` that doesn't inherit from Generator, then it won't be listed as available.

Setting the default generator
=============================

Before we go ahead and code up the generator, we need to tell garak which generator to use by default in this class. This helps save users from always having to specify a model name. We do this in a default class module variable:

.. code-block:: python

    DEFAULT_CLASS = "ReplicateGenerator"

When this generator module is selected using ``--model_type replicate``, with ``replicate`` being the name of the Python module we're working in, the generator loader (in ``garak/generators/__init__.py``) will search for the ``DEFAULT_CLASS`` constant and use its value to determine which class to instantiate.

Core params
===========



Modalities
==========

Important functions
===================

Exception handling
==================

+ backoff

+ None

Testing
=======

Done!
=====

+ send a pr

+ check out the code, replicate.py