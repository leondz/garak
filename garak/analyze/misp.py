#!/usr/bin/env python3

# report probes per tag
# look for untagged probes
# look for tags without description entries

from collections import defaultdict
import importlib
import os

from garak import _plugins

# does this utility really have access to _config?
misp_resource_file = (
    garak._config.transient.basedir / "garak" / "resources" / "misp_descriptions.tsv"
)
misp_descriptions = {}
if os.path.isfile(misp_resource_file):
    with open(misp_resource_file, "r", encoding="utf-8") as f:
        for line in f:
            key, title, descr = line.strip().split("\t")
            misp_descriptions[key] = (title, descr)

probes_per_tag = defaultdict(list)

for plugin_name, active in _plugins.enumerate_plugins("probes"):
    class_name = plugin_name.split(".")[-1]
    module_name = plugin_name.replace(f".{class_name}", "")
    m = importlib.import_module(f"garak.{module_name}")
    c = getattr(m, class_name)
    tags = c.tags
    if tags == []:
        print(f"{plugin_name}: no tags defined")
    for tag in tags:
        if tag not in misp_descriptions:
            print(f"{plugin_name}: tag {tag} undefined in misp_descriptions.tsv")
        probes_per_tag[tag].append(plugin_name)

for misp_tag in misp_descriptions.keys():
    if len(probes_per_tag[misp_tag]) == 0:
        print(f"{misp_tag}: zero probes testing this")
    else:
        if len(probes_per_tag[misp_tag]) == 1:
            print(f"{misp_tag}: only one probe testing this")
        probe_list = ", ".join(probes_per_tag[misp_tag]).replace(" probes.", " ")
        print(f"> {misp_tag}: {probe_list}")
