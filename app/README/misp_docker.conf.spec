# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

#   Version 1.0.0
#
############################################################################
# OVERVIEW
############################################################################
# This file maintains the configuration and state of the scripted MISP inputs.
#
# No Splunk restart is needed for changes to take effect.

[default]
BaseUrl = <string>
* required
* The Base URL of the MISP instance logs will be collected from

AuthKey = <string>
* required
* An authentication key for MISP with permission to read logs

VerifyTls = <boolean>
* required
* Whether to verify MISPs TLS certificate

[misp_user_logs]
LastRun = <number>
* The last time the User log script was run, as a UNIX epoch float
LastId = <number>
* The last event ID that was output for indexing
