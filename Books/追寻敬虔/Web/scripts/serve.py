#!/usr/bin/env python3
"""Serve the generated reader on the loopback interface."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DIST_ROOT = Path(__file__).resolve().parents[1] / "dist"


class ReaderRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()

    chapter = DIST_ROOT / "chapters/05/index.html"
    if not chapter.is_file():
        raise SystemExit("Build output is missing. Run Web/scripts/build.py first.")

    handler = partial(ReaderRequestHandler, directory=str(DIST_ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Reader available at http://127.0.0.1:{args.port}/chapters/05/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
