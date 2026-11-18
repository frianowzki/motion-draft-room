#!/bin/sh
# Rebuild vendor/nightsky.js into a standalone browser bundle: React + framer-motion
# + src/NightSkyBackground.js (the Framer code component, unchanged) driven by
# src/nightsky-entry.jsx. Needs node + npm once; the output is committed, so the
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
cp "$HERE/src/NightSkyBackground.js" "$HERE/src/nightsky-entry.jsx" "$HERE/src/framer-shim.js" .
npx esbuild nightsky-entry.jsx --bundle --minify --format=iife --target=es2019 \
  --alias:framer=./framer-shim.js --define:process.env.NODE_ENV='"production"' \
  --outfile="$HERE/vendor/nightsky.js"
echo "wrote vendor/nightsky.js ($(wc -c < "$HERE/vendor/nightsky.js") bytes)"
