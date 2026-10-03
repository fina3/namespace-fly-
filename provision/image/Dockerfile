# Namespace Custom Image with the whole DOOMFLY simulation pre-baked, so a Devbox
# created from it can start a fly-brain run immediately: no download, no build.
#
#   devbox image build provision/image --name=fly/doomfly --user=devbox
#
# Everything the runs need lives under /opt/fly (not /workspaces, which is the
# Devbox's own volume):
#   /opt/fly/doomfly   DOOMFLY at the pinned commit, with the MaleCNS v1.0 data
#                      (sha256-verified), the prepared graph and the native kernel
#   /opt/fly/venv      Python 3.11 with DOOMFLY's pinned packages
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential clang ca-certificates curl git sudo tar \
 && rm -rf /var/lib/apt/lists/*

# Non-root devbox user with passwordless sudo. Ubuntu 24.04 ships an `ubuntu`
# user at UID 1000; remove it so devbox gets that UID.
RUN userdel -r ubuntu 2>/dev/null || true \
 && useradd --create-home --shell /bin/bash --uid 1000 devbox \
 && echo "devbox ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/devbox \
 && chmod 0440 /etc/sudoers.d/devbox \
 && mkdir -p /workspaces /opt/fly \
 && chown devbox:devbox /workspaces /opt/fly

# uv, then a Python 3.11 managed by uv (DOOMFLY pins numpy 1.24, which needs 3.11).
ENV UV_INSTALL_DIR=/usr/local/bin UV_PYTHON_INSTALL_DIR=/opt/fly/uv-python
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
 && mkdir -p /opt/fly/uv-python && chown devbox:devbox /opt/fly/uv-python

USER devbox
WORKDIR /opt/fly

ARG DOOMFLY_COMMIT=71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33
RUN git clone -q https://github.com/nftechie/doomfly.git /opt/fly/doomfly \
 && git -C /opt/fly/doomfly checkout -q "$DOOMFLY_COMMIT"

# Only the packages the fixed-weight baseline imports, at DOOMFLY's pins.
RUN uv venv -q -p 3.11 /opt/fly/venv \
 && uv pip install -q -p /opt/fly/venv/bin/python \
      numpy==1.24.4 numba==0.61.2 vizdoom==1.3.0 pillow==11.3.0 pyarrow==20.0.0 pandas==2.0.3 scipy==1.10.1

# MaleCNS v1.0 inputs (about 1.1 GB), verified against DOOMFLY's lockfile, then the
# normalized graph, the CSR graph with the retinal projection, and the native kernel.
WORKDIR /opt/fly/doomfly
RUN /opt/fly/venv/bin/python - <<'PY' \
 && /opt/fly/venv/bin/python -m doom.connectome malecns_v1 \
 && /opt/fly/venv/bin/python -m doom.prepare \
 && /opt/fly/venv/bin/python -m doom.audit_data \
 && /opt/fly/venv/bin/python -m doom.build_kernel \
 && rm -rf /opt/fly/doomfly/connectome_data/malecns_v1/edges.feather
from pathlib import Path
import hashlib, json, urllib.request
name = 'malecns_v1'
registry = json.loads(Path('doom/datasets.json').read_text())['datasets'][name]
locked = json.loads(Path(f'data-provenance/{name}/source.lock.json').read_text())
root = Path('connectome_data') / name
root.mkdir(parents=True, exist_ok=True)
for filename, url in registry['files'].items():
    target = root / filename
    partial = target.with_suffix('.download')
    urllib.request.urlretrieve(url, partial)
    partial.replace(target)
    with target.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != locked[filename]['sha256']:
        raise RuntimeError(f'Source checksum mismatch: {filename}')
(root / 'source.lock.json').write_text(json.dumps(locked, indent=2) + '\n')
print('data verified')
PY

# A one-line check that a fresh Devbox can run the model.
COPY --chown=devbox:devbox fly-check /usr/local/bin/fly-check
RUN sudo chmod 0755 /usr/local/bin/fly-check

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    FLY_DOOMFLY=/opt/fly/doomfly FLY_VENV=/opt/fly/venv
WORKDIR /workspaces
