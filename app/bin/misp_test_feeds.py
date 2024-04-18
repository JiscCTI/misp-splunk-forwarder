#!/usr/bin/env python3

"""Test if remote feeds are reachable and output Splunk CIM-compliant Web events"""

# SPDX-FileCopyrightText: 2023-2024 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from configparser import ConfigParser
from json import dumps, loads
from os.path import dirname, join
from sys import exit as sys_exit, path
from time import time
from urllib.parse import urlparse

from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

path.insert(0, join(dirname(__file__), "..", "lib"))
# Import must happen after PATH is altered
from requests import get  # pylint: disable=wrong-import-position

# pylint: disable-next=wrong-import-position
from requests.exceptions import (
    JSONDecodeError,
    RequestException,
)

__author__ = "Joe Pitt"
__copyright__ = "Copyright 2023-2024, Jisc Services Limited"
__email__ = "Joe.Pitt@jisc.ac.uk"
__license__ = "GPL-3.0-only"
__maintainer__ = "Joe Pitt"
__status__ = "Production"
__version__ = "1.0.1"

disable_warnings(InsecureRequestWarning)

JOBS_CONF = "/opt/misp_docker/misp_maintenance_jobs.ini"
jobsConfig = ConfigParser()
jobsConfig.read(JOBS_CONF)

headers = {
    "Authorization": jobsConfig.get("DEFAULT", "AuthKey"),
    "Accept": "application/json",
    "Content-type": "application/json",
    "User-Agent": f"misp_test_feeds/{__version__}",
}

try:
    feeds = get(
        f"{jobsConfig.get('DEFAULT', 'BaseUrl')}/feeds/index",
        headers=headers,
        timeout=5,
        verify=jobsConfig.getboolean("DEFAULT", "VerifyTls"),
    )
except RequestException as e:
    # Shorten exception type to just final class
    EXCEPTION_TYPE = str(type(e))
    if "<class '" in EXCEPTION_TYPE:
        EXCEPTION_TYPE = EXCEPTION_TYPE[8:-2]
        # Benefit of use-maxsplit-arg unclear
        # pylint: disable-next=use-maxsplit-arg
        EXCEPTION_TYPE = EXCEPTION_TYPE.split(".")[-1]
    result = {}
    result["_time"] = time()
    result["action"] = "error"
    result["app"] = "MISP"
    result["authentication_method"] = "api"
    result["reason"] = f"{EXCEPTION_TYPE} getting feed list"
    result["src_host"] = jobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
    sys_exit()

if feeds.status_code == 200:
    for feed in feeds.json():
        if isinstance(feed, dict):
            result = {}
            result["_time"] = time()
            result["error"] = f"Expected dict got {type(feed)}"
            try:
                result["value"] = str(feed)
            except ValueError:
                result["value"] = "Non-serialisable"
            print(dumps(result, sort_keys=True))
            continue
        feed = feed["Feed"]
        if not feed["enabled"] or feed["input_source"] != "network":
            # Skip over disabled and local feeds
            continue

        url = feed["url"]
        if feed["source_format"] == "misp":
            url = f"{url}/manifest.json"

        FEED_HEADERS = None
        if feed["headers"] is not None and len(feed["headers"]) > 0:
            FEED_HEADERS = dict(
                header.split(": ", 1) for header in feed["headers"].split("\r\n")
            )
        try:
            start = time()
            response = get(url, headers=FEED_HEADERS, timeout=5)
            # Web CIM duration is in milliseconds
            duration = round((time() - start) * 1000, 3)
        except RequestException as e:
            # Shorten exception type to just final class
            EXCEPTION_TYPE = str(type(e))
            if "<class '" in EXCEPTION_TYPE:
                EXCEPTION_TYPE = EXCEPTION_TYPE[8:-2]
                EXCEPTION_TYPE = EXCEPTION_TYPE.split(".")[-1]
            error = EXCEPTION_TYPE

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
            # this line can only be called if error is assigned
            result["error_code"] = error  # pylint: disable=used-before-assignment
        if "response" in locals() and response.headers.get("Content-Type") is not None:
            result["http_content_type"] = response.headers.get("Content-Type").split(
                ";"
            )[0]
        result["http_method"] = "GET"
        result["src_host"] = jobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]
        if "response" in locals():
            result["status"] = response.status_code
        if urlParts.path != "":
            result["uri_path"] = urlParts.path
        if urlParts.query != "":
            result["uri_query"] = f"?{urlParts.query}"
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
    result["reason"] = f"{feeds.status_code} - {feeds.reason} getting feed list"
    try:
        result["response"] = feeds.json()
    except JSONDecodeError:
        result["response"] = feeds.content.decode(errors="replace")
    result["src_host"] = jobsConfig.get("DEFAULT", "BaseUrl").split(":")[1][2:]

    print(dumps(result, sort_keys=True))
