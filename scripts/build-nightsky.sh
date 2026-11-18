#!/bin/sh
# Rebuild vendor/pagebg.js into a standalone browser bundle: React + framer-motion
# + the two Framer code components (src/NightSkyBackground.js dark,
# src/ShaderBackgroundLite.js light), both unchanged, driven by src/pagebg-entry.jsx. Needs node + npm once; the output is committed, so the
# Vercel build and the pages themselves stay dependency-free.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
WORK="${SKY_WORK:-/data/home/.hermes/cache/scratch/skybuild}"
mkdir -p "$WORK"
cd "$WORK"
if [ ! -d node_modules/esbuild ]; then
  npm init -y >/dev/null 2>&1
  npm i --silent esbuild react@18 react-dom@18 framer-motion@11
fi
cp "$HERE/src/NightSkyBackground.js" "$HERE/src/ShaderBackgroundLite.js" \
   "$HERE/src/pagebg-entry.jsx" "$HERE/src/framer-shim.js" .
npx esbuild pagebg-entry.jsx --bundle --minify --format=iife --target=es2019 \
  --alias:framer=./framer-shim.js --define:process.env.NODE_ENV='"production"' \
  --outfile="$HERE/vendor/pagebg.js"
echo "wrote vendor/pagebg.js ($(wc -c < "$HERE/vendor/pagebg.js") bytes)"
