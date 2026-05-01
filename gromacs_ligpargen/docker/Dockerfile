# Linux x86_64 image with 32-bit libs so Yale BOSS (ELF i386) can run.
# Use on Apple Silicon: Docker Desktop with Rosetta/QEMU for amd64 (slower but works).
FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        csh \
        libc6:i386 \
        libgcc-s1:i386 \
        libstdc++6:i386 \
        zlib1g:i386 \
        python3 \
        python3-pip \
        python3-venv \
        openbabel \
    && rm -rf /var/lib/apt/lists/*

# LigParGen (vendored copy lives next to this docker/ folder in the build context)
COPY ligpargen_src /opt/ligpargen_src
COPY docker/ligpargen-docker-entrypoint.sh /usr/local/bin/ligpargen-docker-entrypoint.sh
RUN chmod +x /usr/local/bin/ligpargen-docker-entrypoint.sh \
    && python3 -m pip install --no-cache-dir -U pip setuptools wheel \
    && python3 -m pip install --no-cache-dir rdkit \
    && python3 -m pip install --no-cache-dir -e /opt/ligpargen_src

ENV BOSSdir=/boss

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/ligpargen-docker-entrypoint.sh"]
