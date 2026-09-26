# check=skip=InvalidDefaultArgInFrom

# BASE_IMAGE is intentionally required: callers supply the reviewed digest from
# infra/images.lock.env. A fallback tag would make an omitted build argument
# silently mutable.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG DEBIAN_SNAPSHOT=20260909T000000Z
USER root

COPY dependencies/apt-packages.txt /tmp/apt-packages.txt

RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && printf '%s\n' \
      'Types: deb' \
      "URIs: https://snapshot.debian.org/archive/debian/${DEBIAN_SNAPSHOT}/" \
      'Suites: bookworm bookworm-updates' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
      'Check-Valid-Until: no' \
      '' \
      'Types: deb' \
      "URIs: https://snapshot.debian.org/archive/debian-security/${DEBIAN_SNAPSHOT}/" \
      'Suites: bookworm-security' \
      'Components: main' \
      'Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg' \
      'Check-Valid-Until: no' \
      > /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive xargs -r apt-get install -y --no-install-recommends < /tmp/apt-packages.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY dependencies/python-requirements.lock /tmp/python-requirements.lock
RUN if grep -Eq '^[[:space:]]*[^#[:space:]]' /tmp/python-requirements.lock; then \
      python -m pip install --require-hashes -r /tmp/python-requirements.lock; \
    fi

COPY dependencies/package.json dependencies/package-lock.json /opt/sandbox-node-deps/
RUN cd /opt/sandbox-node-deps \
    && npm ci --ignore-scripts --omit=dev --no-audit --no-fund \
    && npm cache clean --force

RUN mkdir -p /workspace /home/hermes \
    && chmod 1777 /workspace /home/hermes \
    && git config --system user.name "Hermes Agent" \
    && git config --system user.email "hermes@localhost"

ENV HOME=/home/hermes \
    CI=true \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_INPUT=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false

WORKDIR /workspace

CMD ["sleep", "infinity"]
