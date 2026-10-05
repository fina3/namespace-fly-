#!/bin/bash
# Set up DOOMFLY on a macOS Devbox (Apple Silicon). macOS boxes cannot use the pre-baked Linux
# image, so this does what provision/image/Dockerfile does, under $HOME/fly. Idempotent.
set -euo pipefail
DOOMFLY_COMMIT=71ecf53d78eaffaf1a57ed7b0ccf5d458abc9f33
FLY=${FLY_HOME:-$HOME/fly}
mkdir -p "$FLY"
export UV_PYTHON_INSTALL_DIR=$FLY/uv-python PATH=$HOME/.local/bin:/opt/homebrew/bin:$PATH

command -v clang++ >/dev/null || { echo "MISSING_TOOL: clang++ (Xcode command line tools)"; exit 127; }
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
command -v uv >/dev/null || { echo "MISSING_TOOL: uv"; exit 127; }

[ -d "$FLY/doomfly/.git" ] || git clone -q https://github.com/nftechie/doomfly.git "$FLY/doomfly"
git -C "$FLY/doomfly" checkout -q "$DOOMFLY_COMMIT"

if [ ! -x "$FLY/venv/bin/python" ]; then
  uv venv -q -p 3.11 "$FLY/venv"
  uv pip install -q -p "$FLY/venv/bin/python" numpy==1.24.4 numba==0.61.2 vizdoom==1.3.0 \
    pillow==11.3.0 pyarrow==20.0.0 pandas==2.0.3 scipy==1.10.1
fi
PY=$FLY/venv/bin/python
$PY -c 'import pygame' 2>/dev/null || uv pip install -q -p "$PY" pygame-ce==2.5.3     # the HUD window for the Live view
[ -s "$FLY/Inter.ttf" ] || curl -sL -o "$FLY/Inter.ttf" 'https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf'
cd "$FLY/doomfly"
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
[ -f outputs/doom/libneural.dylib ] || $PY -m doom.build_kernel
echo "SETUP_OK doomfly=$DOOMFLY_COMMIT python=$($PY --version 2>&1) kernel=$(ls outputs/doom/libneural.* | head -1)"
