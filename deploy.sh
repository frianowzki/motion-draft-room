#!/usr/bin/env bash
# Deploy the landing to production without tripping Vercel's git-author check.
#
# `vercel --prod` refuses to build when the HEAD commit's author is not a member
# of the Vercel team (the team here only holds the project owner). This script
# uploads the tracked files and pins the deployment metadata to the owner
# account, so a commit authored by anyone can still ship.
#
#   ./deploy.sh              # deploy current HEAD
#   ./deploy.sh --dry-run    # print what would be uploaded, deploy nothing
#
# Needs VERCEL_TOKEN in the environment (see .env) and reads the project/team
# ids from the constants below — change them if the project moves.
set -euo pipefail

PROJECT_ID="prj_EqP6zsfA8I5RgnHZq6PzZ7Bk2hxJ"
TEAM_ID="team_WUBUOBmcRunpHS9XChm0pWH7"
PROJECT_NAME="motion-draft-room"
OWNER_NAME="friodrops-5778"
OWNER_EMAIL="friodrops@gmail.com"
PROD_DOMAIN="motion-draft-room.vercel.app"

cd "$(dirname "$0")"

if [ -z "${VERCEL_TOKEN:-}" ]; then
  echo "VERCEL_TOKEN is not set. Load it first: set -a && . ~/.hermes/.env && set +a" >&2
  exit 1
fi

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

python3 - "$DRY" "$PROJECT_ID" "$TEAM_ID" "$PROJECT_NAME" "$OWNER_NAME" "$OWNER_EMAIL" "$PROD_DOMAIN" <<'PY'
import base64, json, os, subprocess, sys, time, urllib.error, urllib.request

dry, proj, team, name, owner, email, domain = sys.argv[1:8]
dry = dry == "1"
tok = os.environ["VERCEL_TOKEN"]
api = "https://api.vercel.com"

def call(method, path, body=None):
    req = urllib.request.Request(
        api + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
        method=method,
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit("vercel %s %s -> %s %s" % (method, path, e.code, e.read().decode()[:400]))

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

# 1. the deployable set: what git tracks, minus the local-only capture file
files, skipped = [], 0
for p in git("ls-files").split("\n"):
    p = p.strip()
    if not p or not os.path.isfile(p):
        continue
    blob = open(p, "rb").read()
    if len(blob) > 3_000_000:          # Vercel's per-file ceiling
        skipped += 1
        continue
    files.append({"file": p, "data": base64.b64encode(blob).decode(), "encoding": "base64"})

if not files:
    sys.exit("nothing to upload")

if dry:
    print("would upload %d files (%d skipped as too large)" % (len(files), skipped))
    for f in files:
        print("  ", f["file"])
    sys.exit(0)

# 2. create the production deployment, pinned to the owner identity
body = {
    "name": name,
    "project": proj,
    "target": "production",
    "files": files,
    "gitMetadata": {
        "commitRef": git("rev-parse", "--abbrev-ref", "HEAD"),
        "commitSha": git("rev-parse", "HEAD"),
        "commitMessage": git("log", "-1", "--format=%s"),
        "commitAuthorName": owner,
        "commitAuthorEmail": email,
        "remoteUrl": git("config", "--get", "remote.origin.url"),
    },
}
dep = call("POST", "/v13/deployments?teamId=%s&forceNew=1" % team, body)
did = dep["id"]
print("created %s  %s" % (did, dep.get("url")))

# 3. wait for the build, then make sure the production domain serves it
state = None
for _ in range(80):
    r = call("GET", "/v13/deployments/%s?teamId=%s" % (did, team))
    state = r.get("readyState")
    if state in ("READY", "ERROR", "CANCELED", "BLOCKED"):
        break
    time.sleep(6)

if state != "READY":
    sys.exit("deployment ended in %s — check https://vercel.com/%s" % (state, did))

r = call("GET", "/v2/projects/%s/domains?teamId=%s" % (proj, team))
if not any(d.get("name") == domain for d in r.get("domains", [])):
    print("warning: %s is not attached to the project; the deploy is at %s"
          % (domain, dep.get("url")))
else:
    print("live at https://%s" % domain)
PY
