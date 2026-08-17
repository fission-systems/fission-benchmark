FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV FISSION_SLEIGH_SPEC_DIR=/sleigh-specs
ENV FISSION_RESOURCE_ROOT=/opt/fission-utils/utils
ENV FISSION_GHIDRA_DATA_DIR=/opt/fission-utils/utils/ghidra-data

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates python3 python3-pip python3-venv tar file \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# FISSION_SOURCE=release (default, CI): bake GitHub Release bundle.
# FISSION_SOURCE=local: image has server only; CLI+utils come from runtime mount
#   via entrypoint.sh (/opt/fission-local).
ARG FISSION_SOURCE=release
ARG FISSION_VERSION=v0.2.1
ENV FISSION_RELEASE_VERSION=${FISSION_VERSION}
ENV FISSION_SOURCE=${FISSION_SOURCE}

RUN set -eux; \
    mkdir -p /opt/fission-utils /opt/fission-local; \
    if [ "$FISSION_SOURCE" = "local" ]; then \
        echo "local-dev" > /opt/fission-release-version; \
        echo "local" > /opt/fission-source; \
        printf '%s\n' \
          '#!/bin/sh' \
          'echo "fission_cli not installed; start with FISSION_SOURCE=local mount (see entrypoint)" >&2' \
          'exit 127' \
          > /usr/local/bin/fission_cli; \
        chmod +x /usr/local/bin/fission_cli; \
    else \
        if [ "$FISSION_VERSION" = "latest" ]; then \
            CLI_URL="https://github.com/fission-systems/Fission/releases/latest/download/fission-linux-x64.tar.gz"; \
        else \
            CLI_URL="https://github.com/fission-systems/Fission/releases/download/${FISSION_VERSION}/fission-linux-x64.tar.gz"; \
        fi; \
        echo "Downloading fission bundle from: $CLI_URL"; \
        curl -fL "$CLI_URL" -o /tmp/fission-bundle.tar.gz; \
        tar --warning=no-unknown-keyword -xzf /tmp/fission-bundle.tar.gz -C /opt/fission-utils; \
        find /opt/fission-utils -name 'fission_cli' -exec cp {} /usr/local/bin/fission_cli \; ; \
        chmod +x /usr/local/bin/fission_cli; \
        /usr/local/bin/fission_cli --version; \
        echo "$FISSION_VERSION" > /opt/fission-release-version; \
        echo "release" > /opt/fission-source; \
        ln -sfn /opt/fission-utils/utils/sleigh-specs /sleigh-specs; \
        test -d /sleigh-specs/languages; \
        test -d /opt/fission-utils/utils/ghidra-data; \
        test -d /opt/fission-utils/utils/signatures; \
        rm /tmp/fission-bundle.tar.gz; \
    fi

# Python FastAPI server
COPY requirements.txt .
RUN python3 -m venv /opt/fission-server-venv \
    && /opt/fission-server-venv/bin/pip install --no-cache-dir -r requirements.txt

COPY server.py pe_helpers.py entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
