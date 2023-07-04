#!/usr/bin/env python
"""Prints a report given a garak report in jsonl"""

import importlib
import sys
import json
import pandas as pd

from datetime import date
from avidtools.datamodels.report import Report
from avidtools.datamodels.components import *

evals = []
meta = None

# load up a .jsonl output file, take in eval and config rows
with open(sys.argv[1], "r") as reportfile:
    for line in reportfile:
        record = json.loads(line.strip())
        if record["entry_type"] == "eval":
            evals.append(record)
        elif record["entry_type"] == "config":
            meta = record
if len(evals)==0:
    ValueError("No evaluations to report!")

# preprocess
for i in range(len(evals)):
    category, module_name, plugin_class_name = evals[i]["probe"].split(".")
    mod = importlib.import_module(f"garak.{category}.{module_name}")
    plugin_instance = getattr(mod, plugin_class_name)()
    evals[i]['probe'] = f"{module_name}.{plugin_class_name}"
    evals[i]['probe_tags'] = plugin_instance.tags

evals_df = pd.DataFrame.from_dict(evals)
evals_df = evals_df.assign(score = lambda x: (x['passed']/x['total'] * 100))
probe_scores = evals_df[['probe','score']].groupby('probe').mean()

# set up a generic report template
report_template = Report()
if meta is not None:
    report_template.affects = Affects(
        developer = [],
        deployer = [meta['model_type']],
        artifacts = [Artifact(
            type = ArtifactTypeEnum.model,
            name = meta['model_name']
        )]
    )

report_template.references = [
    Reference(
        type = 'source',
        label = 'garak, an LLM vulnerability scanner',
        url = 'https://github.com/leondz/garak'
        )
    ]
report_template.reported_date = date.today()

# now build all the reports
all_reports = []
for probe in probe_scores.index:
    report = report_template.copy()
    probe_data = evals_df.query(f"probe==\'{probe}\'")

    print(probe)

    report.description = LangValue(
        lang = 'eng',
        value = f"The model {meta['model_name']} from {meta['model_type']} was evaluated by the Garak LLM Vunerability scanner using the probe `{probe}`."
    )
    report.problemtype = Problemtype(
        classof = ClassEnum.llm,
        type = TypeEnum.measurement,
        description = report.description
    )
    report.metrics = [
        Metric(
            name = '',
            detection_method = Detection(type=MethodEnum.thres, name='Count failed'),
            results = probe_data[['detector','passed','total','score']].to_dict()
        )
    ]

    tags_split = [tag.split(':') for tag in probe_data['probe_tags'][0]]
    report.impact = Impact(
        avid = AvidTaxonomy(
            risk_domain = pd.Series([tag[1].title() for tag in tags_split]).drop_duplicates().tolist(), # unique values
            sep_view = [SepEnum[tag[2]] for tag in tags_split],
            lifecycle_view = [LifecycleEnum['L05']],
            taxonomy_version = ''
        )
    )
    all_reports.append(report)

for r in all_reports:
    print(r.json(indent=4))