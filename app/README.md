# UF for JiscCTI/misp-docker

Collects logs from an instance of the [JiscCTI/misp-docker](https://github.com/JiscCTI/misp-docker/) Docker project.

## Splunk AppInspect

Some AppInspect violations have been accepted due to the nature of this app.

| Rule | File | Justification |
|------|------|---------------|
| check_app_icon_2x_dimensions | NONE | This app is for Universal Forwarders only |
| check_app_icon_2x_is_png | NONE | This app is for Universal Forwarders only |
| check_app_icon_dimensions | NONE | This app is for Universal Forwarders only |
| check_app_icon_is_png | NONE | This app is for Universal Forwarders only |
| check_for_bias_language | METADATA | Only exists within imported modules |
| check_for_indexer_synced_configs | NONE | This app is for Universal Forwarders only |
| check_for_python_script_existence | NONE | All Python scripts are python3 compatible |
| check_hostnames_and_ips | lib/urllib3/util/ssl_match_hostname.py | Only exists within imported modules |
| check_no_default_or_value_before_stanzas | README/misp_docker.conf.spec | This is a spec file for a custom config file |

## Binary File Declaration

The following binary files get installed by PIP when installing the `request` module. Their source code is publicly
available.

### lib/charset_normalizer/md.cpython-37m-x86_64-linux-gnu.so

Part of [Ousret/charset_normalizer](https://github.com/Ousret/charset_normalizer).

### lib/charset_normalizer/md__mypyc.cpython-37m-x86_64-linux-gnu.so

Part of [Ousret/charset_normalizer](https://github.com/Ousret/charset_normalizer).
