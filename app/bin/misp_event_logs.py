#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from configparser import ConfigParser, NoOptionError, NoSectionError
from datetime import datetime, timedelta, timezone

import requests
from requests.exceptions import RequestException, Timeout
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

disable_warnings(InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_FILE = BASE_DIR / "default" / "misp_docker.conf"
LOCAL_CONFIG_FILE = BASE_DIR / "local" / "misp_docker.conf"
JOBS_CONFIG_FILE = Path("/opt/misp_docker/misp_maintenance_jobs.ini")


def load_config(file_paths: list[Path]) -> ConfigParser:
    config = ConfigParser()
    config.read([str(f) for f in file_paths if f.exists()])
    return config


jobs_config = load_config([JOBS_CONFIG_FILE])
app_config = load_config([DEFAULT_CONFIG_FILE, LOCAL_CONFIG_FILE])

if "misp_event_logs" not in app_config.sections():
    app_config.add_section("misp_event_logs")


def get_config_value(config: ConfigParser, section: str, option: str, fallback=None):
    try:
        return config.get(section, option)
    except (NoOptionError, NoSectionError):
        return fallback


def fetch_misp_events():
    misp_url = "https://web:443"
    auth_key = get_config_value(jobs_config, "DEFAULT", "AuthKey")
    verify_tls = jobs_config.getboolean("DEFAULT", "VerifyTls", fallback=False)

    if not misp_url or not auth_key:
        error_event = {"error": "MISP_URL or AuthKey not set in configuration"}
        print(json.dumps(error_event), file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": auth_key,
        "Accept": "application/json",
        "Content-type": "application/json",
        "User-Agent": "misp_event_logs/1.0.0",
    }

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    payload = {"returnFormat": "json", "date_from": yesterday}
    url = f"{misp_url}/events/restSearch"

    try:
        response = requests.post(url, headers=headers, json=payload, verify=verify_tls, timeout=10)
        response.raise_for_status()
    except Timeout:
        error_event = {"error": "Request timed out"}
        print(json.dumps(error_event), file=sys.stderr)
        sys.exit(1)
    except RequestException as e:
        error_event = {"error": f"Request failed: {e}"}
        print(json.dumps(error_event), file=sys.stderr)
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        error_event = {"error": "Failed to parse JSON response"}
        print(json.dumps(error_event), file=sys.stderr)
        sys.exit(1)

    events = data.get("response", [])
    if not events:
        return

    for e in events:
        event = e.get("Event", {})
        output = {
            "id": event.get("id"),
            "info": event.get("info"),
            "date": event.get("date"),
            "org": event.get("Orgc", {}).get("name")
        }
        print(json.dumps(output))


fetch_misp_events()
