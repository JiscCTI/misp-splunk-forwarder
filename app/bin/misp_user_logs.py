#!/usr/bin/env python3

"""Fetch user logs from MISP for indexing by Splunk as CIM-compliant Authentication events"""

# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from configparser import ConfigParser
from datetime import datetime
from json import dumps
from os.path import dirname, join
from sys import path
from time import time
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

try:
    path.insert(0, join(dirname(__file__), "..", "lib"))
    from requests import post
except ImportError:
    raise ImportError("Failed to load requests")

__author__ = "Joe Pitt"
__copyright__ = "Copyright 2023, Jisc Services Limited"
__email__ = "Joe.Pitt@jisc.ac.uk"
__license__ = "GPL-3.0-only"
__maintainer__ = "Joe Pitt"
__status__ = "Production"
__version__ = "1.0.0"

disable_warnings(InsecureRequestWarning)

DefaultAppConfigFile = join(dirname(__file__), "..", "default", "misp_docker.conf")
JobsConfigFile = "/opt/misp_docker/misp_maintenance_jobs.ini"
LocalAppConfigFile = join(dirname(__file__), "..", "local", "misp_docker.conf")
JobsConfig = ConfigParser()
JobsConfig.read(JobsConfigFile)
AppConfig = ConfigParser()
AppConfig.read(
    (
        DefaultAppConfigFile,
        LocalAppConfigFile,
    )
)
if "misp_user_logs" not in AppConfig.sections():
    AppConfig.add_section("misp_user_logs")

Since = AppConfig.getfloat("misp_user_logs", "LastRun", fallback=0)

Headers = {
    "Authorization": JobsConfig.get("DEFAULT", "AuthKey"),
    "Accept": "application/json",
    "Content-type": "application/json",
    "User-Agent": "misp_user_logs/{}".format(__version__),
}

Options = {
    "created": Since,
    "model": "User",
}

logs = post(
    "{}/admin/logs/index".format(JobsConfig.get("DEFAULT", "BaseUrl")),
    json=Options,
    headers=Headers,
    verify=JobsConfig.getboolean("DEFAULT", "VerifyTls", fallback=False),
)

Now = datetime.now().timestamp()

if logs.status_code == 200:
    for log in logs.json():
        if type(log) != dict:
            result = {}
            result["_time"] = time()
            result["error"] = "Expected dict got {}".format(type(log))
            try:
               result["value"] = str(log)
            except Exception:
                result["value"] = "Non-serialisable"
            print(dumps(result, sort_keys=True))
            continue
        log = log["Log"]

        if int(log["id"]) <= AppConfig.getint("misp_user_logs", "lastId", fallback=0):
            continue
        AppConfig.set("misp_user_logs", "lastId", log["id"])

        log["_time"] = datetime.strptime(
            log["created"], "%Y-%m-%d %H:%M:%S"
        ).timestamp()
        log.pop("created")

        log["type"] = log.pop("action")

        if log["type"] in ("auth", "login"):
            log["action"] = "success"
        elif log["type"] in ("auth_fail", "login_fail"):
            log["action"] = "failure"

        if log["type"] in ("auth", "auth_fail"):
            log["authentication_method"] = "api"
        elif log["type"] in ("login", "login_fail"):
            log["authentication_method"] = "web"

        log.pop("type")

        log["app"] = "MISP"
        log["reason"] = log.pop("title")
        log["src_ip"] = log.pop("ip")
        log["src"] = log["src_ip"]
        log["user"] = log.pop("email")
        log["user_bunit"] = log.pop("org")
        log["user_id"] = log.pop("model_id")
        log["dest"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]
        log["dest_host"] = log["dest"]

        if "HTTP method:" in log["change"]:
            act = {}
            fields = log["change"].split("\n")
            i = 0
            for field in fields:
                field = field.split(": ")
                if i == 0:
                    act["method"] = field[1]
                else:
                    act["uri"] = field[1]
                i = i + 1
            log["act"] = act
        log.pop("change")

        log.pop("description")
        log.pop("id")
        log.pop("model")

        print(dumps(log, sort_keys=True))

    AppConfig.set("misp_user_logs", "LastRun", str(Now))
    with open(LocalAppConfigFile, "w") as f:
        AppConfig.write(f)
else:
    result = {}
    result["_time"] = time()
    result["error"] = "{} - {} getting logs".format(
        logs.status_code, logs.reason
    )
    try:
        result["response"] = logs.json()
    except Exception:
        result["response"] = logs.content.decode(errors="replace")
    print(dumps(result, sort_keys=True))
