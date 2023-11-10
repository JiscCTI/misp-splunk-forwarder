# SPDX-FileCopyrightText: 2023 Jisc Services Limited
# SPDX-FileContributor: Joe Pitt
#
# SPDX-License-Identifier: GPL-3.0-only

FROM splunk/universalforwarder:9.0.6
LABEL org.opencontainers.image.title="misp-splunk-forwarder" org.opencontainers.image.version=v1.0.0\
    org.opencontainers.image.ref.name="misp-splunk-forwarder"\
    org.opencontainers.image.description="Self configuring Splunk Universal Forwarder for MISP."\
    org.opencontainers.image.authors="Jisc <CTI.Analysts@jisc.ac.uk"\
    org.opencontainers.image.base.name="hub.docker.com/splunk/universalforwarder"
ENV HEC_URI=https://splunk.example.com:8088 HEC_KEY=00000000-1111-2222-3333-444444444444 HEC_SSL=true HEC_VERIFY=false\
    INDEX=default FQDN=misp.example.com HTTPS_PORT=443 MISP_KEY=000111222333444555666777888999aaabbcccdd\
    MISP_VERIFY=false
VOLUME "/opt/splunkforwarder/etc/apps/misp_docker/local" "/opt/splunkforwarder/var/lib/splunk/fishbucket"\
    "/var/logs/MISP"
COPY --chown=ansible:ansible configure.py /sbin/configure.py
COPY --chown=ansible:ansible entrypoint.sh /sbin/entrypoint.sh
COPY --chown=ansible:ansible app/ /opt/splunkforwarder/etc/apps/misp_docker
RUN /bin/python -m pip install --target=/opt/splunkforwarder/etc/apps/misp_docker/lib\
    -r /opt/splunkforwarder/etc/apps/misp_docker/requirements.txt &&\
    find /opt/splunkforwarder/etc/apps/misp_docker/ -type d -exec chmod 755 {} \; || true &&\
    find /opt/splunkforwarder/etc/apps/misp_docker/ -type f -exec chmod 644 {} \; || true &&\
    chmod +x /sbin/entrypoint.sh
