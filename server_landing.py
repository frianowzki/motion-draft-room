#!/usr/bin/env python3
"""Local preview of the split: /  -> landing.html, /app -> app.html, /api/signals -> prod passthrough."""
import http.server, socketserver, os, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ROUTES = {"/": "landing.html", "/app": "app.html", "/app/": "app.html"}
PROD = "https://motion-draft-room.vercel.app"


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ROUTES:
            body = open(os.path.join(ROOT, ROUTES[path]), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/signals":
            try:
                with urllib.request.urlopen(PROD + "/api/signals", timeout=20) as r:
                    body = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_error(502, str(e))
            return
        super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8099"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), H) as s:
        print(f"serving {ROOT} on {port}", flush=True)
        s.serve_forever()
