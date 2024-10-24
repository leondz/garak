garak.policy
============

This module represents objects related to policy scanning. 

Policy scanning in garak attempts to work out what the target's content policy
is, before running a security scan. 

It's important to know what target content policy is because we only really have
a useful/successful hit or breach if we're able to get a model to do something that
it otherwise wouldn't. It may be exciting to discover a model gives instructions for
e.g. cooking meth if the request is encoded in base64, but if in fact the model gives
the instructions when simply asked directly "print instructions for cooking meth", the
use of base64 necessarily an exploit in this output category - the model is acting 
the same.

Garak's policy support follows a typology of different behaviours, each describing
a different behaviour. By default this typology is stored in ``data/policy/policy_typology.json``.

A policy scan is conducted by invoking garak with the ``--policy_scan`` switch.
When this is requested, a separate scan runs using all policy probes within garak.
Policy probes are denoted by a probe class asserting ``policy_probe=True``.
A regular probewise harness runs the scan, though reporting is diverted to a separate
policy report file. After completion, garak estimates a policy based on policy probe
results, and writes this to both main and poliy reports.


.. automodule:: garak.policy
   :members:
   :undoc-members:
   :show-inheritance:   
