#!/usr/bin/env python
"""Prints a report given a garak report in jsonl"""

import importlib
import json
import pandas as pd

from datetime import date
import avidtools.datamodels.report as ar
import avidtools.datamodels.components as ac

# load up a .jsonl output file, take in eval and config rows
class Report:
    def __init__(self):
        self.records = []
        self.metadata = None

    def load(self, report_location: str):

        self.report_location = report_location
        with open(report_location, "r") as reportfile:
            for line in reportfile:
                record = json.loads(line.strip())
                self.records.append(record)

    def get_evaluations(self):
        evals = []

        for record in self.records:
            if record["entry_type"] == "eval":
                evals.append(record)
            elif record["entry_type"] == "config":
                self.metadata = record
        if len(evals) == 0:
            raise ValueError("No evaluations to report 🤷")

        # preprocess
        for i in range(len(evals)):
            module_name, plugin_class_name = evals[i]["probe"].split(".")
            mod = importlib.import_module(f"garak.probes.{module_name}")

            evals[i]["probe"] = f"{module_name}.{plugin_class_name}"
            plugin_instance = getattr(mod, plugin_class_name)()
            evals[i]["probe_tags"] = plugin_instance.tags

        evals_df = pd.DataFrame.from_dict(evals)
        self.evaluations = evals_df.assign(score=lambda x: (x["passed"] / x["total"] * 100))
        self.scores = self.evaluations[["probe", "score"]].groupby("probe").mean()

    def export(self): # TODO: add html format

        # set up a generic AVID report template
        report_template = ar.Report()
        if self.metadata is not None:
            report_template.affects = ac.Affects(
                developer = [],
                deployer = [self.metadata["model_type"]],
                artifacts = [
                    ac.Artifact(
                        type = ArtifactTypeEnum.model,
                        name = self.metadata["model_name"]
                    )
                ],
            )

        report_template.references = [
            ac.Reference(
                type="source",
                label="garak, an LLM vulnerability scanner",
                url="https://github.com/leondz/garak",
            )
        ]
        report_template.reported_date = date.today()

        # now build all the reports
        all_reports = []
        for probe in self.scores.index:
            report = report_template.copy()
            probe_data = self.evaluations.query(f"probe=='{probe}'")

            report.description = ac.LangValue(
                lang="eng",
                value=f"The model {self.metadata['model_name']} from {self.metadata['model_type']} was evaluated by the Garak LLM Vunerability scanner using the probe `{probe}`.",
            )
            report.problemtype = avid.components.Problemtype(
                classof = ClassEnum.llm,
                type = TypeEnum.measurement, 
                description = report.description
            )
            report.metrics = [
                ac.Metric(
                    name="",
                    detection_method=avid.components.Detection(
                        type=MethodEnum.thres,
                        name="Count failed"
                    ),
                    results=probe_data[["detector", "passed", "total", "score"]].reset_index().to_dict(),
                )
            ]
            all_tags = probe_data.iloc[0]["probe_tags"]
            if all_tags == all_tags: # check for NaN
                tags_split = [tag.split(":") for tag in all_tags if tag.startswith("avid")] # supports only avid taxonomy for now
                report.impact = ac.Impact(
                    avid = ac.AvidTaxonomy(
                        risk_domain = pd.Series([tag[1].title() for tag in tags_split]).drop_duplicates().tolist(),  # unique values
                        sep_view = [SepEnum[tag[2]] for tag in tags_split],
                        lifecycle_view = [LifecycleEnum["L05"]],
                        taxonomy_version = "",
                    )
                )
            all_reports.append(report)

        # save final output
        write_location = self.report_location.replace(".report",".avid")
        with open(write_location, "w") as f:
            f.writelines(r.json()+"\n" for r in all_reports)