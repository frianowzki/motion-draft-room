"""Connect X at /api/xauth/... — authorise once, get a signed session.

  GET /api/xauth/status    -> who is this browser? {"connected": false} or the user
  GET /api/xauth/start      -> 302 to X (Authorization Code + PKCE, scope=users.read)
  GET /api/xauth/callback   -> exchange the code, store a session cookie, hand control back
  GET /api/xauth/logout     -> drop the cookie

A handle typed into a box is not an identity: anyone can file under someone else's
name. Here the handle on a receipt is the one X returned for the account that
completed the OAuth round trip, and the access token never reaches the browser.

Vercel maps api/xauth/<step>.py to /api/xauth/<step>, so each of those files is a
thin wrapper over this module.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from http.server import BaseHTTPRequestHandler  # noqa: E402

# The module is vendored next to the handlers because a Vercel function only gets
# its own directory on sys.path; api/xauth_lib.py is the same file for api/receipts.py.
import xauth_lib as xl

class _Entry(BaseHTTPRequestHandler):
    """What Vercel hands a handler. Only keeps the class import honest."""

    def log_message(self, *a):
        pass


Base = _Entry


def _origin(headers):
    host = (headers.get("x-forwarded-host") or headers.get("host") or "").split(",")[0].strip()
    proto = (headers.get("x-forwarded-proto") or "https").split(",")[0].strip()
    return f"{proto}://{host}" if host else ""


def _headers(handler):
    return {k: v for k, v in handler.headers.items()}


def status(handler):
    user = xl.session_of(handler.headers)
    if user:
        payload = {"connected": True, "configured": True, "user": user}
    else:
        payload = {
            "connected": False,
            "configured": xl.configured(),
            "reason": None if xl.configured()
            else "X_CLIENT_ID / X_SESSION_SECRET are not set on this deployment",
        }
    body, code, _ = xl.json_response(200, payload)
    _send(handler, body, code, "application/json; charset=utf-8")


def start(handler):
    if not xl.configured():
        html, code, _ = xl.page(
            "Connect X is not configured yet",
            "<p>This deployment is missing <code>X_CLIENT_ID</code> or "
            "<code>X_SESSION_SECRET</code>, so there is no app to authorise against. "
            "Nothing is broken in your browser.</p>",
            status=503,
        )
        return _send_page(handler, html, code)
    verifier = xl.new_verifier()
    state = xl.b64url(os.urandom(16))
    # The state cookie carries the verifier's hash and the nonce, so the callback can
    # prove the round trip started here even though the URL it lands on is public.
    sealed = xl.seal({"n": state, "v": verifier, "exp": int(__import__("time").time()) + 600})
    params = {
        "response_type": "code",
        "client_id": xl.client_id(),
        "redirect_uri": xl.redirect_uri(_origin(_headers(handler))),
        "scope": "users.read tweet.read",
        "state": state,
        "code_challenge": xl.challenge(verifier),
        "code_challenge_method": "S256",
    }
    url = xl.AUTHORIZE + "?" + urllib.parse.urlencode(params)
    handler.send_response(302)
    handler.send_header("Location", url)
    handler.send_header("Set-Cookie", xl.state_cookie(sealed))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()


def _send_page(handler, html, code=200, cookies=()):
    _send(handler, html.encode(), code, "text/html; charset=utf-8", cookies)


def _send(handler, body, code, ctype, cookies=()):
    handler.send_response(code)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Cache-Control", "no-store")
    for c in cookies:
        handler.send_header("Set-Cookie", c)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _fail(handler, message, status=400):
    html, code, _ = xl.page(
        "Could not connect X",
        f"<p>{message}</p><p><a href='/'>Back to the room</a></p>",
        status=status,
    )
    _send_page(handler, html, code)


def callback(handler):
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(handler.path).query)
    code = (qs.get("code") or [""])[0]
    state = (qs.get("state") or [""])[0]
    denied = (qs.get("error") or [""])[0]

    if denied:
        # Cancelling on X's own screen is a normal outcome, not an error to shout about.
        return _fail(handler, f"X reported <code>{denied}</code>. Nothing was connected.", 200)

    cookie = xl.unseal(xl.cookies_of(handler.headers).get(xl.STATE_COOKIE, ""))
    if not cookie or not state or cookie.get("n") != state:
        return _fail(handler, "That sign-in did not start here (state mismatch or expired). "
                              "Start again from the room — it takes one tap.")

    verifier = cookie.get("v") or ""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": xl.redirect_uri(_origin(_headers(handler))),
        "code_verifier": verifier,
        "client_id": xl.client_id(),
    }
    token = xl.client_secret()
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "motion-draft-room"}
    if token:
        import base64

        basic = base64.b64encode(f"{xl.client_id()}:{token}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    req = urllib.request.Request(xl.TOKEN, method="POST",
                                 data=urllib.parse.urlencode(data).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            tok = __import__("json").loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode(errors="replace")
        return _fail(handler, "X refused the token exchange. " f"<code>{e.code}</code> {detail}")

    access = tok.get("access_token")
    if not access:
        return _fail(handler, "X returned no access token.")

    try:
        me = xl.fetch_me(access)
    except Exception as e:  # noqa: BLE001 - report, never crash the callback
        return _fail(handler, f"Could not read the account from X: {e}")

    handle = str(me.get("username") or "")
    if not handle:
        return _fail(handler, "X returned an account with no username.")

    user = {
        "handle": handle,
        "name": str(me.get("name") or handle)[:40],
        "id": str(me.get("id") or ""),
        "avatar": str(me.get("profile_image_url") or ""),
    }
    html, code_out, _ = xl.page(
        f"Connected as @{handle}",
        "<p>This tab did its job. You can close it.</p>"
        "<script>try{window.opener&&window.opener.postMessage({type:'mdr-oauth',ok:true},'*')}"
        "catch(e){};setTimeout(function(){try{window.close()}catch(e){}},900)</script>"
        "<p><a href='/'>Back to the room</a></p>",
    )
    _send_page(handler, html, code_out, (xl.session_cookie(user), xl.clear(xl.STATE_COOKIE)))


def logout(handler):
    html, code, _ = xl.page(
        "Signed out",
        "<p>The session cookie is gone. Receipts already filed stay in the book.</p>"
        "<p><a href='/'>Back to the room</a></p>",
    )
    _send_page(handler, html, code, (xl.clear(xl.SESSION_COOKIE),))


