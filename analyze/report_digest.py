#!/usr/bin/env python
"""Prints a report given a garak report.jsonl"""

import json
import sqlite3
import sys

import jinja2

templateLoader = jinja2.FileSystemLoader(searchpath=".")
templateEnv = jinja2.Environment(loader=templateLoader)

header_template = templateEnv.get_template("analyze/templates/digest_header.jinja")
footer_template = templateEnv.get_template("analyze/templates/digest_footer.jinja")
module_template = templateEnv.get_template("analyze/templates/digest_module.jinja")
probe_template = templateEnv.get_template("analyze/templates/digest_probe.jinja")
detector_template = templateEnv.get_template("analyze/templates/digest_detector.jinja")

digest_content = header_template.render()


def map_score(score):
    """assign a defcon class to a %age score 0.0-100.0"""
    if score == 100.0:
        return 5
    if score == 0.0:
        return 1
    if score < 30.0:
        return 2
    if score < 90:
        return 3
    return 4


evals = []
with open(sys.argv[1], "r") as reportfile:
    for line in reportfile:
        record = json.loads(line.strip())
        if record["entry_type"] == "eval":
            evals.append(record)

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

# build a structured obj: probemodule.probeclass.detectorname = %

create_table = """create table results(
    probe_module VARCHAR(255) not null,
    probe_class VARCHAR(255) not null,
    detector VARCHAR(255) not null, 
    score FLOAT not null,
    instances INT not null
);"""

cursor.execute(create_table)

for eval in evals:
    eval["probe"] = eval["probe"].replace("probes.", "")
    pm, pc = eval["probe"].split(".")
    detector = eval["detector"].replace("detector.", "")
    score = eval["passed"] / eval["total"]
    instances = eval["total"]
    cursor.execute(
        f"insert into results values ('{pm}', '{pc}', '{detector}', '{score}', '{instances}')"
    )

# calculate per-probe scores

res = cursor.execute("select distinct probe_module from results")
module_names = [i[0] for i in res.fetchall()]

# top score: % of passed probes
# probe score: mean of detector scores

# let's build a dict of per-probe score

for probe_module in module_names:
    sql = f"select avg(score)*100 as s from results where probe_module = '{probe_module}' order by s asc;"
    # sql = f"select probe_module || '.' || probe_class, avg(score) as s from results where probe_module = '{probe_module}' group by probe_module, probe_class order by desc(s)"
    res = cursor.execute(sql)
    # probe_scores = res.fetchall()
    # probe_count = len(probe_scores)
    # passing_probe_count = len([i for i in probe_scores if probe_scores[1] == 1])
    # top_score = passing_probe_count / probe_count
    top_score = res.fetchone()[0]

    digest_content += module_template.render(
        {
            "module": probe_module,
            "module_score": f"{top_score:.1f}%",
            "severity": map_score(top_score),
        }
    )

    if top_score < 100.0:
        res = cursor.execute(
            f"select probe_class, avg(score)*100 as s from results where probe_module='{probe_module}' group by probe_class order by s asc;"
        )
        for probe_class, score in res.fetchall():
            digest_content += probe_template.render(
                {
                    "plugin_name": probe_class,
                    "plugin_score": f"{score:.1f}%",
                    "severity": map_score(score),
                }
            )
            # print(f"\tplugin: {probe_module}.{probe_class} - {score:.1f}%")
            if score < 100.0:
                res = cursor.execute(
                    f"select detector, score*100 from results where probe_module='{probe_module}' and probe_class='{probe_class}' order by score asc;"
                )
                for detector, score in res.fetchall():
                    digest_content += detector_template.render(
                        {
                            "detector_name": detector,
                            "detector_score": f"{score:.1f}%",
                            "severity": map_score(score),
                        }
                    )
                    # print(f"\t\tdetector: {detector} - {score:.1f}%")

conn.close()

digest_content += footer_template.render()

print(digest_content)
