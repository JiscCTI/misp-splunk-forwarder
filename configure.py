#!/usr/bin/env python3

"""Auto configuration of the misp_docker app based on environment variables"""

# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

from argparse import ArgumentParser
from configparser import ConfigParser

__author__ = "Joe Pitt"
__copyright__ = "Copyright 2023, Jisc Services Limited"
__email__ = "Joe.Pitt@jisc.ac.uk"
__license__ = "GPL-3.0-only"
__maintainer__ = "Joe Pitt"
__status__ = "Production"
__version__ = "1.0.0"

parser = ArgumentParser()
# HTTP Event Collector options
parser.add_argument("-hu", "--hec-uri", required=True, dest="hecUri")
parser.add_argument("-hk", "--hec-key", required=True, dest="hecKey")
parser.add_argument(
    "-hv", "--hec-verify", choices=["true", "false"], required=True, dest="hecVerify"
)
parser.add_argument(
    "-hs", "--hec-ssl", choices=["true", "false"], required=True, dest="hecSsl"
)
parser.add_argument("-in", "--index", required=True, dest="index")
# MISP options
parser.add_argument("-mu", "--misp-uri", required=True, dest="mispUri")
parser.add_argument("-mk", "--misp-key", required=True, dest="mispKey")
parser.add_argument(
    "-mv",
    "--misp-verify",
    choices=["true", "false"],
    required=True,
    dest="mispVerify",
)
# Input options
parser.add_argument("-f", "--fqdn", required=True, dest="fqdn")

args = parser.parse_args()

if args.hecUri in ("", "https://splunk.example.com:8088"):
    raise ValueError("HEC_URI not configured, cannot start.")
if args.hecKey in ("", "00000000-1111-2222-3333-444444444444"):
    raise ValueError("HEC_KEY not configured, cannot start.")
if args.mispUri.startswith("https://:") or args.mispUri.startswith(
    "https://misp.example.com:"
):
    raise ValueError("(MISP) FQDN not configured, cannot start.")
if args.mispKey in ("", "000111222333444555666777888999aaabbcccdd"):
    raise ValueError("MISP_KEY not configured, cannot start.")
if args.fqdn in ("", "misp.example.com"):
    raise ValueError("(MISP) FQDN not configured, cannot start.")

inputsConf = "/opt/splunkforwarder/etc/apps/misp_docker/local/inputs.conf"
inputs = ConfigParser()
inputs.read(inputsConf)
if "default" not in inputs.sections():
    inputs.add_section("default")
inputs.set("default", "host", args.fqdn)
inputs.set("default", "index", args.index)
with open(inputsConf, "w") as f:
    inputs.write(f)

outputsConf = "/opt/splunkforwarder/etc/apps/misp_docker/local/outputs.conf"
outputs = ConfigParser()
# preserve camel casing of option names - Splunk options are case sensitive
outputs.optionxform = str
outputs.read(outputsConf)
if "httpout" not in outputs.sections():
    outputs.add_section("httpout")
outputs.set("httpout", "httpEventCollectorToken", args.hecKey)
outputs.set("httpout", "uri", args.hecUri)
outputs.set("httpout", "sslVerifyServerCert", args.hecVerify)
outputs.set("httpout", "sslVerifyServerName", args.hecVerify)
outputs.set("httpout", "useSSL", args.hecSsl)
with open(outputsConf, "w") as f:
    outputs.write(f)

appConf = "/opt/splunkforwarder/etc/apps/misp_docker/local/misp_docker.conf"
app = ConfigParser()
app.read(appConf)
if "default" not in app.sections():
    app.add_section("default")
app.set("default", "baseUrl", args.mispUri)
app.set("default", "authKey", args.mispKey)
app.set("default", "verifyTls", args.mispVerify)
with open(appConf, "w") as f:
    app.write(f)
