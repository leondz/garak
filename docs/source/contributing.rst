Contributing
============

Getting ready
-------------

Garak's codebase is managed using github.
The best and only way to contribute to garak is to start by getting a copy of the source code.
You can use github's fork function to do this, which makes a copy of the garak codebase under your github user.
In there, you can edit code and build.
Once you're done, make a pull request to the main repo and describe what you've done -- and we'll take it from there!


Connecting with the garak team & community
------------------------------------------

If you're going to contribute, it's a really good idea to reach out, so you have a source of help nearby, and so that we can make sure your valuable coding time is spent efficiently as a contributor.
There are a number of ways you can reach out to us:

* GitHub discussions: `<https://github.com/leondz/garak/discussions>`
* Twitter: `<https://twitter.com/garak_llm>`
* Discord: `<https://discord.gg/uVch4puUCs>`

We'd love to help, and we're always interested to hear how you're using garak.

Developing your own plugins
---------------------------

The recipe isn't outlandish:

* Take a look at how other plugins do it
* Start a new module inheriting from one of the base classes, e.g. :class:`garak.probes.base.Probe`
* Override as little as possible.


Guides to writing plugins
-------------------------

So you'd like to build a new garak plugin? Great! Here are our tutorials.

* :doc:`Building a garak generator <contributing.generator>` -- step-by-step guide to building an interface for a real API-based model service



Testing
-------

You can test your code in a few ways:

* Start an interactive Python session
   * Import the model, e.g. `import garak.probes.mymodule`
   * Instantiate the plugin, e.g. `p = garak.probes.mymodule.MyProbe()`
* Get `garak` to list all the plugins of the type you're writing, with `--list_probes`, `--list_detectors`, or `--list_generators`: `python3 -m garak --list_probes`
* Run a scan with test plugins
   * For probes, try a blank generator and always.Pass detector: `python3 -m garak -m test.Blank -p mymodule -d always.Pass`
   * For detectors, try a blank generator and a blank probe: `python3 -m garak -m test.Blank -p test.Blank -d mymodule`
   * For generators, try a blank probe and always.Pass detector: `python3 -m garak -m mymodule -p test.Blank -d always.Pass`


garak supports pytest tests in garak/tests. You can run these with ``python -m pytest tests/`` from the root directory.
All the tests should pass for any code there's a pull request for, and all tests must pass in any PR before it can be merged.

Please write running tests to validate any new components or functions that you add.
They're pretty straightforward - you can look at the existing code to get an idea of how to write these.

