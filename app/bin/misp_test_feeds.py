#!/usr/bin/env python3

"""Test if remote feeds are reachable and output Splunk CIM-compliant Web events"""

# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from configparser import ConfigParser
from json import dumps, loads
from os.path import dirname, join
from sys import path
from time import time
from urllib.parse import urlparse
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

try:
    path.insert(0, join(dirname(__file__), "..", "lib"))
    from requests import get
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

Headers = {
    "Authorization": JobsConfig.get("DEFAULT", "AuthKey"),
    "Accept": "application/json",
    "Content-type": "application/json",
    "User-Agent": "misp_test_feeds/{}".format(__version__),
}

try:
    feeds = get(
        "{}/feeds/index".format(JobsConfig.get("DEFAULT", "BaseUrl")),
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
    result["reason"] = "{} getting feed list".format(exceptionType)
    result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
    exit()

if feeds.status_code == 200:
    for feed in feeds.json():
        feed = feed["Feed"]
        if not feed["enabled"] or feed["input_source"] != "network":
            # Skip over disabled and local feeds
            continue

        url = feed["url"]
        if feed["source_format"] == "misp":
            url = "{}/manifest.json".format(url)

        Headers = None
        if feed["headers"] is not None:
            Headers = dict(
                header.split(": ", 1) for header in feed["headers"].split("\r\n")
            )
        try:
            start = time()
            response = get(url, headers=Headers, timeout=5)
            # Web CIM duration is in milliseconds
            duration = round((time() - start) * 1000, 3)
        except Exception as e:
            # Shorten exception type to just final class
            exceptionType = str(type(e))
            if "<class '" in exceptionType:
                exceptionType = exceptionType[8:-2]
                exceptionType = exceptionType.split(".")[-1]
            error = exceptionType

        urlParts = urlparse(url)
        result = {}
        # Web CIM fields
        result["_time"] = time()
        result["dest"] = feed["name"]
        result["dest_bunit"] = feed["provider"]
        result["dest_id"] = feed["id"]
        result["dest_host"] = urlParts.hostname
        if urlParts.port is not None:
            result["dest_port"] = urlParts.port
        if "duration" in locals():
            result["duration"] = duration
        if "error" in locals():
            result["error_code"] = error
        if "response" in locals() and response.headers.get("Content-Type") is not None:
            result["http_content_type"] = response.headers.get("Content-Type").split(
                ";"
            )[0]
        result["http_method"] = "GET"
        result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]
        if "response" in locals():
            result["status"] = response.status_code
        if urlParts.path != "":
            result["uri_path"] = urlParts.path
        if urlParts.query != "":
            result["uri_query"] = "?{}".format(urlParts.query)
        result["url_domain"] = urlParts.hostname
        result["url_length"] = len(url)
        result["url"] = url

        # MISP-specific fields
        if feed["rules"] is not None:
            result["rules"] = loads(feed["rules"])

        print(dumps(result, sort_keys=True))
else:
    result = {}
    result["_time"] = time()
    result["action"] = "error"
    result["app"] = "MISP"
    result["authentication_method"] = "api"
    result["reason"] = "{} - {} getting feed list".format(
        feeds.status_code, feeds.reason
    )
    result["src_host"] = JobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
