#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Sample app with a GENUINE first-run dead-end — the GauntletGate golden fixture.

The "core feature" (Create) is reachable ONLY when the backend dependency is
present. With the dependency ABSENT — the brand-new-user reality — the core
action is DISABLED and the setup copy tells the user to go install it themselves,
with no in-product path forward. That is a first-run dead-end, and it is NOT
mocked: it is driven by the real dependency check in `backend_present()`.

Dependency model: env var GAUNTLET_SAMPLE_BACKEND must be a non-empty value
(stand-in for "a model/inference server / API is configured"). Absent or empty
=> dependency ABSENT => dead-end.

Run:  python app.py <port>
"""

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def backend_present() -> bool:
    return bool(os.environ.get("GAUNTLET_SAMPLE_BACKEND", "").strip())


def page() -> str:
    if backend_present():
        return (
            "<!doctype html><meta charset=utf-8><title>Sample</title>"
            "<h1>Welcome back</h1>"
            "<button id='core-action'>Create your first thing</button>"
            "<p id='status'>Backend connected — you're ready to go.</p>"
        )
    # First run / dependency ABSENT: the dead-end.
    return (
        "<!doctype html><meta charset=utf-8><title>Sample</title>"
        "<h1>Set up your AI</h1>"
        "<button id='core-action' disabled>Create your first thing</button>"
        "<p id='status' data-deadend='true'>No backend found. Install it yourself "
        "and restart the app — see the docs.</p>"
    )


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8799
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
