<!--
SPDX-FileCopyrightText: 2023 Jisc Services Limited
SPDX-FileContributor: Joe Pitt

SPDX-License-Identifier: GPL-3.0-only
-->
# MISP Docker Forwarder App for Splunk

[![CodeFactor](https://www.codefactor.io/repository/github/jisccti/misp-splunk-forwarder/badge)](https://www.codefactor.io/repository/github/jisccti/misp-splunk-forwarder)
[![AppInspect](https://github.com/JiscCTI/misp-splunk-forwarder/actions/workflows/appinspect.yml/badge.svg)](https://github.com/JiscCTI/misp-splunk-forwarder/actions/workflows/appinspect.yml)
[![Image Build](https://github.com/JiscCTI/misp-splunk-forwarder/actions/workflows/image-build.yml/badge.svg)](https://github.com/JiscCTI/misp-splunk-forwarder/actions/workflows/image-build.yml)

Collects logs from an instance of the JiscCTI/misp-docker Docker project.

## Requirements

* Splunk 9.x
* A configured HTTP Event Collector
* An instance of JiscCTI/misp-docker

## Usage

1. Configure Docker to forward logs to the HTTP Event Collector by adding the settings in `docker-daemon.json` to
    `/etc/docker/daemon.json`, configuring HEC URI, Key and target index.
2. Add the required environment variables to your `.env` file:
    * `SPLUNK_PASSWORD` A password to use when creating the admin account on the Splunk Universal Forwarder.
    * `SPLUNK_HEC_URI` The same HTTP Event Collector URI configured in Docker.
    * `SPLUNK_HEC_KEY` The same HTTP Event Collector key configured in Docker.
    * `SPLUNK_HEC_SSL` Case-sensitive `true` or `false` for if HTTPS is needed for the HTTP Event Collector.
    * `SPLUNK_HEC_VERIFY` Case-sensitive `true` or `false` for whether HTTPS certificate should be verified for the HTTP
        Event Collector.
    * `SPLUNK_INDEX` The index logs should be written to.
    * `SPLUNK_MISP_AUTHKEY` An AuthKey from MISP which can read logs, e.g. from an account with the `admin` role.
    * `SPLUNK_MISP_VERIFY` Case-sensitive `true` or `false` for whether HTTPS certificate should be verified for MISP.
3. Add the `splunk_forwarder` services from `docker-compose-snip.yml` to your `docker-compose.yml` file.
4. Start the Universal Forwarder: `docker compose up -d`
