"""Vercel function: /api/xauth/callback. Logic lives in oauth.py next to this file."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import oauth  # noqa: E402


class handler(oauth.Base):  # noqa: N801 - Vercel looks for this name
    def do_GET(self):
        oauth.callback(self)
