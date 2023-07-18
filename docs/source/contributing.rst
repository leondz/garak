Contributing
=====



Developing your own plugins
---------------------------

* Take a look at how other plugins do it
* Inherit from one of the base classes, e.g. `garak.probes.base.TextProbe`
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
