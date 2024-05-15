Contributing
============

Getting ready
-------------

The best and only way to contribute to garak is to start by getting a copy of the source code.
You can use github's fork function to do this.
Once you're done, make a pull request to the main repo and describe what you've done -- and we'll take it from there!

Developing your own plugins
---------------------------

* Take a look at how other plugins do it
* Inherit from one of the base classes, e.g. :class:`garak.probes.base.Probe`
* Override as little as possible
* You can test the new code in at least two ways:
   * Start an interactive Python session
      * Import the model, e.g. `import garak.probes.mymodule`
      * Instantiate the plugin, e.g. `p = garak.probes.mymodule.MyProbe()`
   * Run a scan with test plugins
      * For probes, try a blank generator and always.Pass detector: `python3 -m garak -m test.Blank -p mymodule -d always.Pass`
      * For detectors, try a blank generator and a blank probe: `python3 -m garak -m test.Blank -p test.Blank -d mymodule`
      * For generators, try a blank probe and always.Pass detector: `python3 -m garak -m mymodule -p test.Blank -d always.Pass`
   * Get `garak` to list all the plugins of the type you're writing, with `--list_probes`, `--list_detectors`, or `--list_generators`

Tests
-----

garak supports pytest tests in garak/tests. You can run these with ``python -m pytest tests/`` from the root directory.
Please write running tests to validate any new components or functions that you add.
They're pretty straightforward - you can look at the existing code to get an idea of how to write these.

Finding help and connecting with the garak community
----------------------------------------------------

There are a number of ways you can reach out to us! We'd love to help and we're always interested to hear how you're using garak.

* GitHub discussions: `<https://github.com/leondz/garak/discussions>`
* Twitter: `<https://twitter.com/garak_llm>`
* Discord: `<https://discord.gg/uVch4puUCs>`