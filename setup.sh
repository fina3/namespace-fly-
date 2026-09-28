#!/bin/bash
# Bootstrap one devbox: pinned DOOMFLY checkout, Python 3.11 env, MaleCNS v1.0
# data (checksum-verified), prepared CSR graph and native kernel.
# Idempotent: every step is skipped when its output already exists.
set -euo pipefail

DOOMFLY_COMMIT=71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33
WORK=${WORK:-/workspaces}
DOOMFLY=$WORK/doomfly
export UV_PYTHON_INSTALL_DIR=$WORK/uv-python  # /usr/local/uv is root-owned

command -v uv >/dev/null || { echo "MISSING_TOOL: uv"; exit 127; }
if ! command -v clang++ >/dev/null; then
  sudo apt-get update -qq && sudo apt-get install -y -qq clang >/dev/null
fi

if [ ! -d "$DOOMFLY/.git" ]; then
  git clone -q https://github.com/nftechie/doomfly.git "$DOOMFLY"
fi
git -C "$DOOMFLY" fetch -q --depth 1 origin "$DOOMFLY_COMMIT" 2>/dev/null || true
git -C "$DOOMFLY" checkout -q "$DOOMFLY_COMMIT"

# Only the packages the fixed-weight baseline imports, at DOOMFLY's pins.
# brian2 (reference model only) is deliberately skipped.
if [ ! -x "$WORK/venv/bin/python" ]; then
  uv venv -q -p 3.11 "$WORK/venv"
  uv pip install -q -p "$WORK/venv/bin/python" numpy==1.24.4 numba==0.61.2 vizdoom==1.3.0 \
    pillow==11.3.0 pyarrow==20.0.0 pandas==2.0.3 scipy==1.10.1
fi
PY=$WORK/venv/bin/python

cd "$DOOMFLY"
# Download + sha256-verify the three MaleCNS v1.0 files (DOOMFLY README recipe).
$PY - <<'PY'
from pathlib import Path
import hashlib, json, urllib.request
name = 'malecns_v1'
registry = json.loads(Path('doom/datasets.json').read_text())['datasets'][name]
locked = json.loads(Path(f'data-provenance/{name}/source.lock.json').read_text())
root = Path('connectome_data') / name
root.mkdir(parents=True, exist_ok=True)
for filename, url in registry['files'].items():
    target = root / filename
    if not target.exists():
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
[ -f connectome_data/malecns_v1/normalized/edges.arrow ] || $PY -m doom.connectome malecns_v1
[ -f outputs/doom/malecns_v1/graph.npz ] || $PY -m doom.prepare
[ -f outputs/doom/libneural.so ] || $PY -m doom.build_kernel
echo "SETUP_OK doomfly=$DOOMFLY_COMMIT"
