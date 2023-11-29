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
    INDEX=default FQDN=misp.example.com HTTPS_PORT=443
VOLUME "/opt/splunkforwarder/etc/" "/opt/splunkforwarder/var/" "/opt/misp_docker/"
COPY --chown=ansible:ansible configure.py /sbin/configure.py
COPY --chown=ansible:ansible entrypoint.sh /sbin/entrypoint.sh
COPY --chown=ansible:ansible app/ /opt/misp_docker_app
RUN /bin/python -m pip install --target=/opt/misp_docker_app/lib -r /opt/misp_docker_app/requirements.txt &&\
    find /opt/misp_docker_app -type d -exec chmod 755 {} \; || true &&\
    find /opt/misp_docker_app -type f -exec chmod 644 {} \; || true &&\
    chmod +x /sbin/entrypoint.sh
