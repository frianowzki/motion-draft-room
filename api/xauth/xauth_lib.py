"""Session signing for /api/xauth and /api/receipts.

A player is identified by the X account they proved they own, not by a handle typed
into a box. The flow is OAuth 2.0 Authorization Code + PKCE (public client, no
secret), then this module signs a short-lived session so a second request can carry
the identity without trusting anything the browser says about itself.

Design notes, because they decide what the code is allowed to do:

- The state cookie is HttpOnly, SameSite=Lax, and holds an HMAC of the nonce and
  verifier. The URL the callback arrives on is attacker-controlled, so nothing in
  the query string is trusted on its own: without the cookie there is no session.
- The verifier never leaves the server, and the token exchange happens server-side.
  An access token that reaches the browser is an access token a script can lift.
- Sessions are stateless HMAC tokens. That means rotating X_SESSION_SECRET logs
  everyone out, which is the honest tradeoff for not running a database.
"""

# This module is vendored twice on purpose: api/xauth_lib.py (imported by
# api/receipts.py) and api/xauth/xauth_lib.py (imported by the /api/xauth steps).
# A Vercel Python function only gets its own directory on sys.path, so a nested
# function cannot import from its parent. Change both — or copy one over the other.

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

try:  # Vercel installs requirements.txt; keep local imports working if it is absent.
    from urllib.parse import quote, urlencode
except ImportError:  # pragma: no cover
    from urllib import quote, urlencode  # type: ignore

SESSION_COOKIE = "mdr_session"
STATE_COOKIE = "mdr_oauth"
SESSION_TTL = 60 * 60 * 24 * 30  # a receipt book does not need shorter, and a player
                                 # who has to log in again to check their own call will not.

AUTHORIZE = "https://twitter.com/i/oauth2/authorize"
TOKEN = "https://api.twitter.com/2/oauth2/token"
ME = "https://api.twitter.com/2/users/me"


# ---------------------------------------------------------------- config helpers
def _env(name):
    return (os.environ.get(name) or "").strip()


def client_id():
    return _env("X_CLIENT_ID")


def client_secret():
    # Optional. A public client does not need one; if X issues one we use it, because
    # confidential clients get a stricter token exchange for free.
    return _env("X_CLIENT_SECRET")


def secret():
    """Signing key. Without it there are no sessions and the endpoint says so."""
    return _env("X_SESSION_SECRET")


def redirect_uri(request_origin):
    """Where X sends the browser back.

    X requires an exact match against the callback registered in the app, so this is
    configurable rather than derived: a preview deployment has a different hostname
    from production, and guessing would produce a redirect_uri mismatch that looks
    like a bug in X's console.
    """
    return _env("X_REDIRECT_URI") or (request_origin.rstrip("/") + "/api/xauth/callback")


def configured():
    return bool(client_id() and secret())


# ---------------------------------------------------------------- pkce + cookies
def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def new_verifier() -> str:
    return b64url(secrets.token_bytes(48))


def challenge(verifier: str) -> str:
    return b64url(hashlib.sha256(verifier.encode()).digest())


def _sign(payload: str) -> str:
    return b64url(hmac.new(secret().encode(), payload.encode(), hashlib.sha256).digest())


def seal(payload: dict) -> str:
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    return body + "." + _sign(body)


def unseal(token: str):
    """Verify-and-decode. Returns None for anything tampered with, truncated or
    signed with a different secret - a failure is never an exception the caller
    has to remember to catch."""
    if not token or not secret() or "." not in token:
        return None
    body, _, sig = token.rpartition(".")
    if not hmac.compare_digest(sig, _sign(body)):
        return None
    try:
        payload = json.loads(b64url_decode(body))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("exp") and float(payload["exp"]) < time.time():
        return None
    return payload


def cookie(name, value, max_age, secure=True):
    parts = [
        f"{name}={value}",
        "Path=/",
        f"Max-Age={int(max_age)}",
        "HttpOnly",
        "SameSite=Lax",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def state_cookie(value, max_age=600):
    return cookie(STATE_COOKIE, value, max_age)


def session_cookie(user, max_age=SESSION_TTL):
    token = seal({"u": user, "exp": int(time.time()) + max_age})
    return cookie(SESSION_COOKIE, token, max_age)


def clear(name):
    return f"{name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax; Secure"


def cookies_of(headers) -> dict:
    raw = headers.get("Cookie") or ""
    out = {}
    for part in raw.split(";"):
        if "=" not in part:
            continue
        k, _, v = part.partition("=")
        out[k.strip()] = v.strip()
    return out


def session_of(headers):
    """The signed-in user, or None. Never raises: an unauthenticated visit is normal."""
    if not secret():
        return None
    payload = unseal(cookies_of(headers).get(SESSION_COOKIE, ""))
    if not payload:
        return None
    user = payload.get("u") or {}
    handle = str(user.get("handle") or "")
    # Re-check the shape on the way out: a session minted by an older build must not
    # become a way to put arbitrary text on a public page.
    if not handle or len(handle) > 15 or not all(c.isalnum() or c == "_" for c in handle):
        return None
    return user


# ---------------------------------------------------------------- X calls
def api_get(url, access_token):
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "motion-draft-room",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"{}")


def fetch_me(access_token):
    data = api_get(f"{ME}?user.fields=profile_image_url,username,name", access_token)
    return (data or {}).get("data") or {}


# ---------------------------------------------------------------- rendering
def page(title, body, *, status=200, extra_headers=()):
    """A tiny server-rendered page for the OAuth round trip.

    These are the only pages the API layer owns: the app itself is one static file,
    so the callback has to answer with something readable when it lands in a new
    tab. It hands control straight back with postMessage and a redirect.
    """
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Motion Draft Room</title>
<style>
 body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#050506;
   color:#f4f5f2;font:14px/1.6 Inter,system-ui,sans-serif}}
 .box{{max-width:380px;padding:28px;border-radius:16px;background:rgba(255,255,255,.04);
   box-shadow:inset 0 0 0 1px rgba(255,255,255,.09);text-align:center}}
 h1{{font-size:16px;margin:0 0 10px;font-weight:600}}
 p{{color:#a8a8b4;margin:0 0 14px}}
 a{{color:#c8ff4d;text-decoration:none;font-weight:500}}
 code{{font:11px ui-monospace,monospace;background:rgba(255,255,255,.06);padding:2px 5px;border-radius:4px}}
</style></head><body><div class="box"><h1>{title}</h1>{body}</div></body></html>"""
    return html, status, extra_headers


def json_response(code, payload, extra_headers=()):
    import json as _json

    body = _json.dumps(payload).encode()
    return body, code, [("Content-Type", "application/json; charset=utf-8")] + list(extra_headers)
