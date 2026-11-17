"""Resolve a Motion creator name to an X account, strictly.

Motion's public leaderboard exposes only id, name, position and delta. There is
no handle, avatar, banner or social link anywhere in it, so anything the UI
shows beyond a name has to be resolved against X and proven before use.

Guessing is cheap and mostly wrong: coffeezilla resolves to an unrelated private
account, markcuban to a 3k-follower impostor, daveportnoy to an empty shell. So
a candidate is only accepted when all three hold:

  1. the account is verified,
  2. the normalised names agree (one contains the other),
  3. it has at least MIN_FOLLOWERS followers.

Anything else resolves to None and the UI falls back to initials. A wrong
profile is worse than no profile: it puts someone else's face and follower
count under a creator's Motion rank.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

API = "https://api.fxtwitter.com/{handle}"
UA = {"User-Agent": "motion-draft-room/1.0 (+https://motion-draft-room.vercel.app)"}
MIN_FOLLOWERS = 1000
MAX_TRIES = 4
SLEEP = 0.15


def candidates(name: str) -> list[str]:
    """Handle guesses, most likely first. Kept deliberately small."""
    n = name.strip().lower()
    out: list[str] = []
    for c in (
        "".join(ch for ch in n if ch.isalnum() or ch in "_."),
        n.replace(" ", ""),
        n.replace(" ", "_"),
        n.replace(" ", "") + "1",
    ):
        if c and c not in out:
            out.append(c)
    return out[:MAX_TRIES]


def normalise(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def fetch(handle: str) -> dict | None:
    try:
        req = urllib.request.Request(API.format(handle=handle), headers=UA)
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None
    return body.get("user") if body.get("code") == 200 else None


def accept(name: str, user: dict) -> bool:
    a, b = normalise(name), normalise(user.get("name", ""))
    if not a or not b:
        return False
    # A single-word Motion name is too weak a signal: "Andy" matches Andy
    # Cohen the TV host, "Jason" matches Jason Calacanis. Skip them.
    if " " not in name.strip():
        return False
    if not (a in b or b in a):
        return False
    if not (user.get("verification") or {}).get("verified"):
        return False
    return int(user.get("followers") or 0) >= MIN_FOLLOWERS


def resolve(name: str) -> dict | None:
    for handle in candidates(name):
        user = fetch(handle)
        if user and accept(name, user):
            return {
                "handle": user["screen_name"],
                "displayName": user.get("name"),
                "followers": int(user.get("followers") or 0),
                "avatar": user.get("avatar_url") or None,
                "banner": user.get("banner_url") or None,
                "description": user.get("description") or None,
                "url": f"https://x.com/{user['screen_name']}",
                "website": user.get("website") or None,
                "verified": True,
                "match": "verified-name-followers",
            }
        time.sleep(SLEEP)
    return None


def resolve_all(names: list[str], cache: dict | None = None) -> dict:
    """Resolve every name, reusing a cache so repeat builds stay cheap."""
    out: dict = {}
    for name in names:
        if cache and name in cache:
            out[name] = cache[name]
            continue
        out[name] = resolve(name)
    return out


if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "data/signals.json"
    names = [c["name"] for c in json.load(open(src, encoding="utf-8"))["creators"]]
    res = resolve_all(names)
    hit = sum(1 for v in res.values() if v)
    print(f"{hit}/{len(names)} creators matched a verified X account")
    json.dump(res, open("data/profiles.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("wrote data/profiles.json")
