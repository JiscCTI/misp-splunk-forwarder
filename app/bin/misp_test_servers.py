#!/usr/bin/env python3

"""Test if remote servers are reachable and output Splunk CIM-compliant Authentication events"""

# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from configparser import ConfigParser
from json import dumps, loads
from os.path import dirname, join
from sys import path
from time import time
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

try:
    path.insert(0, join(dirname(__file__), "..", "lib"))
    from requests import get, post
    from requests.exceptions import ReadTimeout
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

JobsConfigFile = "/opt/misp_docker/misp_maintenance_jobs.ini"
JobsConfig = ConfigParser()
JobsConfig.read(JobsConfigFile)

action = {1: "success", 2: "error", 3: "error", 4: "failure", 5: "error", 6: "error"}
reason = {
    1: "test-passed",
    2: "network-error",
    3: "app-error",
    4: "invalid-auth-key",
    5: "password-change-required",
    6: "terms-not-accepted",
}

Headers = {
    "Authorization": JobsConfig.get("DEFAULT", "AuthKey"),
    "Accept": "application/json",
    "Content-type": "application/json",
    "User-Agent": "misp_test_servers/{}".format(__version__),
}

try:
    servers = get(
        "{}/servers/index".format(JobsConfig.get("DEFAULT", "BaseUrl")),
        headers=Headers,
        timeout=5,
        verify=JobsConfig.getboolean("DEFAULT", "VerifyTls"),
    )
except Exception as e:
    # Shorten exception type to just final class
    exceptionType = str(type(e))
    if "<class '" in exceptionType:
        exceptionType = exceptionType[8:-2]
        exceptionType = exceptionType.split(".")[-1]
    result = {}
    result["_time"] = time()
    result["action"] = "error"
    result["app"] = "MISP"
    result["authentication_method"] = "api"
    result["reason"] = "{} getting server list".format(exceptionType)
    result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
    exit()

if servers.status_code == 200:
    for server in servers.json():
        if type(server) != dict:
            result = {}
            result["_time"] = time()
            result["error"] = "Expected dict got {}".format(type(server))
            try:
                result["value"] = str(server)
            except Exception:
                result["value"] = "Non-serialisable"
            print(dumps(result, sort_keys=True))
            continue
        if not server["Server"]["push"] and not server["Server"]["pull"]:
            # Skip over disabled servers
            continue
        baseUrlParts = server["Server"]["url"].split(":")
        result = {}
        start = time()
        try:
            testResult = post(
                "{}/servers/testConnection/{}".format(
                    JobsConfig.get("DEFAULT", "BaseUrl"), server["Server"]["id"]
                ),
                headers=Headers,
                timeout=5,
                verify=JobsConfig.getboolean("DEFAULT", "VerifyTls"),
            ).json()
            remoteUser = post(
                "{}/servers/getRemoteUser/{}".format(
                    JobsConfig.get("DEFAULT", "BaseUrl"), server["Server"]["id"]
                ),
                headers=Headers,
                timeout=5,
                verify=JobsConfig.getboolean("DEFAULT", "VerifyTls"),
            ).json()
        except ReadTimeout:
            testResult = {"status": 2}
            remoteUser = {}
        duration = round(time() - start, 3)

        # Authentication CIM fields
        result["_time"] = time()
        result["action"] = action[testResult["status"]]
        result["app"] = "MISP"
        result["authentication_method"] = "api"
        result["dest"] = server["Server"]["name"]
        result["dest_bunit"] = server["RemoteOrg"]["name"]
        result["dest_host"] = baseUrlParts[1][2:]
        result["dest_id"] = int(server["Server"]["id"])
        if len(baseUrlParts) == 3:
            result["dest_port"] = int(baseUrlParts[2])
        elif baseUrlParts[0] == "https":
            result["dest_port"] = 443
        else:
            result["dest_port"] = 80
        result["dest_tls"] = baseUrlParts[0] == "https"
        result["duration"] = duration
        result["reason"] = reason[testResult["status"]]
        result["response_time"] = duration
        result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]
        result["src_bunit"] = server["Organisation"]["name"]
        if "User" in remoteUser:
            result["user"] = remoteUser["User"]
            result["user_role"] = remoteUser["Role name"]
            result["user_sync_flag"] = remoteUser["Sync flag"] == "Yes"
        elif testResult["status"] == 1:
            # if connection test also failed that keep that error reason
            result["action"] = "error"
            result["reason"] = "cannot-get-remote-user"

        # MISP-specific fields
        result["pull_enabled"] = server["Server"]["pull"]
        result["pull_rules"] = loads(server["Server"]["pull_rules"])
        result["push_enabled"] = server["Server"]["push"]
        result["push_rules"] = loads(server["Server"]["push_rules"])
        result["self_signed_allowed"] = server["Server"]["self_signed"]

        if "local_version" in testResult:
            result["version_local"] = testResult["local_version"]
        if "mismatch" in testResult:
            result["version_mismatch"] = testResult["mismatch"]
        if "version" in testResult:
            result["version_remote"] = testResult["version"]

        print(dumps(result, sort_keys=True))
else:
    result = {}
    result["_time"] = time()
    result["action"] = "error"
    result["app"] = "MISP"
    result["authentication_method"] = "api"
    result["reason"] = "{} - {} getting server list".format(
        servers.status_code, servers.reason
    )
    try:
        result["response"] = servers.json()
    except Exception:
        result["response"] = servers.content.decode(errors="replace")
    result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
