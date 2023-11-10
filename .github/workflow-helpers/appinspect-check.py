#!/usr/bin/env python3

"""Check the output of AppInspect, discounting any accepted findings"""

# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from json import load

__author__ = "Joe Pitt"
__copyright__ = "Copyright 2023, Jisc Services Limited"
__email__ = "Joe.Pitt@jisc.ac.uk"
__license__ = "GPL-3.0-only"
__maintainer__ = "Joe Pitt"
__status__ = "Production"
__version__ = "1.0.0"

with open("report.json", "r") as f:
    Results = load(f)
with open(".github/workflow-helpers/appinspect-accepted.json", "r") as f:
    Accepted = load(f)
Issues = []


for Report in Results["reports"]:
    for Group in Report["groups"]:
        for Check in Group["checks"]:
            if Check["result"] in (
                "error",
                "failure",
                "warning",
            ):
                accepted = False
                for Accept in Accepted:
                    if Check["name"] == Accept["name"]:
                        for Message in Check["messages"]:
                            # force string comparison due to anomalous handling of None in GitHub Actions
                            if "{}".format(Message["message_filename"]) == "{}".format(
                                Accept["message_filename"]
                            ):
                                accepted = True
                                break
                if not accepted:
                    for Message in Check["messages"]:
                        Issues.append(
                            {
                                "result": Check["result"],
                                "name": Check["name"],
                                "message": Message["message"],
                                "message_filename": "{}".format(
                                    Message["message_filename"]
                                ),
                            }
                        )

if len(Issues) > 0:
    for Issue in Issues:
        if Issue["message_filename"] == "None":
            print(
                "[{}] {} - {}".format(Issue["result"], Issue["name"], Issue["message"])
            )
        else:
            print(
                "[{}] {} in {} - {}".format(
                    Issue["result"],
                    Issue["name"],
                    Issue["message_filename"],
                    Issue["message"],
                )
            )
    exit(1)
