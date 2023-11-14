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

response = post(
    "{}/admin/logs/index".format(JobsConfig.get("DEFAULT", "BaseUrl")),
    json=Options,
    headers=Headers,
    verify=JobsConfig.getboolean("DEFAULT", "VerifyTls", fallback=False),
)

Now = datetime.now().timestamp()

for Log in response.json():
    Log = Log["Log"]

    if int(Log["id"]) <= AppConfig.getint("misp_user_logs", "lastId", fallback=0):
        continue
    AppConfig.set("misp_user_logs", "lastId", Log["id"])

    Log["_time"] = datetime.strptime(Log["created"], "%Y-%m-%d %H:%M:%S").timestamp()
    Log.pop("created")

    Log["type"] = Log.pop("action")

    if Log["type"] in ("auth", "login"):
        Log["action"] = "success"
    elif Log["type"] in ("auth_fail", "login_fail"):
        Log["action"] = "failure"

    if Log["type"] in ("auth", "auth_fail"):
        Log["authentication_method"] = "api"
    elif Log["type"] in ("login", "login_fail"):
        Log["authentication_method"] = "web"

    Log.pop("type")

    Log["app"] = "MISP"
    Log["reason"] = Log.pop("title")
    Log["src_ip"] = Log.pop("ip")
    Log["src"] = Log["src_ip"]
    Log["user"] = Log.pop("email")
    Log["user_bunit"] = Log.pop("org")
    Log["user_id"] = Log.pop("model_id")
    Log["dest"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]
    Log["dest_host"] = Log["dest"]

    if "HTTP method:" in Log["change"]:
        act = {}
        fields = Log["change"].split("\n")
        i = 0
        for field in fields:
            field = field.split(": ")
            if i == 0:
                act["method"] = field[1]
            else:
                act["uri"] = field[1]
            i = i + 1
        Log["act"] = act
    Log.pop("change")

    Log.pop("description")
    Log.pop("id")
    Log.pop("model")

    print(dumps(Log, sort_keys=True))

AppConfig.set("misp_user_logs", "LastRun", str(Now))
with open(LocalAppConfigFile, "w") as f:
    AppConfig.write(f)
