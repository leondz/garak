Let's build a generator!
========================

Let's build a garak generator. In garak, generators provide abstraction between the main code base and a dialogue system. That system is often an LLM, but can be anything that accepts and returns text (or text plus some other modality).

In this example, we're going to build a module for interfacing with the LLMs hosted by `Replicate <https://replicate.com/>`_, using the Replicate API (`docs <https://replicate.com/docs/get-started/python>`_).

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

Setting the default generator
=============================

Before we go ahead and code up the generator, we need to tell garak which generator to use by default in this class. This helps save users from always having to specify a model name. We do this in a default class module variable:

.. code-block:: python

    default_class = "ReplicateGenerator"

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