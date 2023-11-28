garak
=====

garak._config
-------------

This module holds config values.

These are broken into the following major categories:

* system: options that don't affect the security assessment
* run: options that describe how a garak run will be conducted
* plugins: config for plugins (generators, probes, detectors, buffs)
* transient: internal values local to a single garak execution

Config values are loaded in the following priority (lowest-first):

* Plugin defaults in the code
* Core config: from ``garak/resources/garak.core.yaml``; not to be overridden
* Site config: from ``garak/garak.site.yaml``
* Runtime config: from an optional config file specified manually, via e.g. CLI parameter
* Command-line options

Code
^^^^

.. automodule:: garak._config
   :members:
   :undoc-members:
   :show-inheritance:   


garak._plugins
--------------

This module manages plugin enumeration and loading. 
There is one class per plugin in garak.
Enumerating the classes, with e.g. ``--list_probes`` on the command line, means importing each module.
Therefore, modules should do as little as possible on load, and delay
intensive activities (like loading classifiers) until a plugin's class is instantiated.

Code
^^^^

.. automodule:: garak._plugins
   :members:
   :undoc-members:
   :show-inheritance:   

