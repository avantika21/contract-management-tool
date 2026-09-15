#!/usr/bin/env bash
# Builds the Lambda dependency layer: third-party packages (pg8000) plus
# our shared src/common code, so every handler can `import common.db`
# etc. via the layer's /opt/python without duplicating it into each
# function's zip. Pure-Python deps only - no Docker/cross-compile needed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAYER_DIR="$REPO_ROOT/build/layer/python"

rm -rf "$REPO_ROOT/build/layer"
mkdir -p "$LAYER_DIR"

python3 -m pip install -r "$REPO_ROOT/src/common/requirements.txt" -t "$LAYER_DIR" --quiet
cp -r "$REPO_ROOT/src/common" "$LAYER_DIR/common"

echo "Layer built at $LAYER_DIR"
