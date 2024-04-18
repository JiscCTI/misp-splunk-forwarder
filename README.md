<!--
SPDX-FileCopyrightText: 2023-2024 Jisc Services Limited
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

See [here](./docs/misp-splunk-forwarder.md) for usage instructions.
