#!/bin/sh
# Vercel build (zero dependencies).
#
# The front-end lives on `main`; the data lives on the `data` branch and is rewritten
# every 4 hours by GitHub Actions. We pull the branch as a tarball at build time so the
# deploy carries a real data snapshot, then /api/signals serves the freshest copy for
# browsers — so the page still shows new slots without waiting for a redeploy.
set -eu

REPO="${DATA_REPO:-frianowzki/motion-draft-room}"
rm -rf public
mkdir -p public

cp landing.html public/index.html
cp app.html public/app.html

# the landing hero ribbon ships local card art; without this the cards render empty
if [ -d img ]; then
  cp -R img public/img
fi

# self-hosted type: Clash Grotesk (display), Satoshi (body), Gambetta (accent)
if [ -d fonts ]; then
  cp -R fonts public/fonts
fi

# pre-bundled Framer code component (nightsky.js = the linked NightSkyBackground
# wrapped with react + framer-motion by esbuild; rebuild with npm run sky)
if [ -d vendor ]; then
  cp -R vendor public/vendor
fi

# The repository is private, so the anonymous tarball host answers 404. Use a
# fine-grained read-only token when the build environment has one; without it the
# deploy just leans on /api/signals at request time.
GH_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -n "$GH_TOKEN" ]; then
  GHAUTH="Authorization: Bearer $GH_TOKEN"
else
  GHAUTH="X-Anon: 1"
fi

if curl -fsSL --max-time 30 -H "$GHAUTH" \
    "https://codeload.github.com/${REPO}/tar.gz/refs/heads/data" -o /tmp/data.tgz; then
  mkdir -p /tmp/databranch
  tar -xzf /tmp/data.tgz -C /tmp/databranch --strip-components=1
  if [ -f /tmp/databranch/data/signals.json ]; then
    cp /tmp/databranch/data/signals.json public/signals.json
    SLOTS=$(ls -1 /tmp/databranch/data/snapshots 2>/dev/null | wc -l | tr -d ' ')
    echo "bundled signals.json with ${SLOTS} snapshot(s)"
  else
    echo "WARN: data branch has no signals.json yet; page will rely on /api/signals"
  fi
  # X profiles ride along when the collector has published them; the board works
  # without this file, the hover card just cannot confirm an account
  if [ -f /tmp/databranch/data/profiles.json ]; then
    cp /tmp/databranch/data/profiles.json public/profiles.json
  fi
else
  echo "WARN: could not fetch data branch; page will rely on /api/signals"
fi

ls -la public
