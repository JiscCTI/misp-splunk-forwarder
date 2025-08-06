#!/usr/bin/env python3

"""Check the output of AppInspect, discounting any accepted findings"""

# SPDX-FileCopyrightText: 2023-2025 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from json import load
from sys import exit as sys_exit

__author__ = "Joe Pitt"
__copyright__ = "Copyright 2023-2025, Jisc Services Limited"
__email__ = "Joe.Pitt@jisc.ac.uk"
__license__ = "GPL-3.0-only"
__maintainer__ = "Joe Pitt"
__status__ = "Production"
__version__ = "1.0.1"


def main():  # pylint: disable=too-many-branches
    """Main Function"""

    with open("report.json", "r", encoding="utf-8") as results_file, open(
        ".github/workflow-helpers/appinspect-accepted.json", "r", encoding="utf-8"
    ) as accepted_file:
        results = load(results_file)
        accepted_findings = load(accepted_file)
    unaccepted_findings = []

    for report in results["reports"]: # pylint: disable=too-many-nested-blocks
        for group in report["groups"]:
            for check in group["checks"]:
                if check["result"] in (
                    "error",
                    "failure",
                    "warning",
                ):
                    finding_accepted = False
                    for accepted_finding in accepted_findings:
                        if check["name"] == accepted_finding["name"]:
                            for message in check["messages"]:
                                # force string comparison due to anomalous handling of None in
                                # GitHub Actions
                                if (
                                    f"{accepted_finding['message_filename']}" == "None"
                                    or f"{message['message_filename']}"
                                    == f"{accepted_finding['message_filename']}"
                                ):
                                    finding_accepted = True
                                    break
                    if not finding_accepted:
                        for message in check["messages"]:
                            unaccepted_findings.append(
                                {
                                    "result": check["result"],
                                    "name": check["name"],
                                    "message": message["message"],
                                    "message_filename": f"{message['message_filename']}",
                                }
                            )

    if len(unaccepted_findings) > 0:
        for unaccepted_finding in unaccepted_findings:
            if unaccepted_finding["message_filename"] == "None":
                print(
                    f"[{unaccepted_finding['result']}] {unaccepted_finding['name']} - "
                    f"{unaccepted_finding['message']}"
                )
            else:
                print(
                    f"[{unaccepted_finding['result']}] {unaccepted_finding['name']} in "
                    f"{unaccepted_finding['message_filename']} - {unaccepted_finding['message']}"
                )
        sys_exit(1)


if __name__ == "__main__":
    main()
