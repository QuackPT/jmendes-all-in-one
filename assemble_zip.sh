#!/usr/bin/env bash
set -euo pipefail

# assemble_zip.sh
# Create a distributable pack zip containing manifest.json and overrides
# Usage: ./assemble_zip.sh [output.zip]

OUT=${1:-jmendes-all-in-one-pack.zip}
WORKDIR="pack_tmp"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

# Copy manifest and overrides
cp manifest.json "$WORKDIR/"
mkdir -p "$WORKDIR/overrides"
cp -r overrides/* "$WORKDIR/overrides/"

# Include assets if present
if [ -d assets ]; then
  mkdir -p "$WORKDIR/assets"
  cp -r assets/* "$WORKDIR/assets/"
fi

# Zip it up
rm -f "$OUT"
( cd "$WORKDIR" && zip -r "../$OUT" . )

# Clean up
rm -rf "$WORKDIR"

echo "Created $OUT"
