"""Serve a built registry on loopback for the Cloudflare Tunnel."""
from __future__ import annotations

import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import parse_qs

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PUBLIC_PATH = re.compile(
    rf"/(?:en/?)?|/(?:en/)?skills/{SLUG.pattern}/?|/assets/registry\.(?:css|js)"
    rf"|/downloads/{SLUG.pattern}\.zip"
)


class RegistryHandler(SimpleHTTPRequestHandler):
    def missing(self, path: str):
        page = "en/404.html" if path == "/en" or path.startswith("/en/") else "404.html"
        try:
            file = (Path(self.directory) / page).open("rb")
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return None
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        return file

    def send_head(self):
        path, _, query = self.path.partition("?")
        if path in ("/", "/en", "/en/"):
            skills = parse_qs(query, keep_blank_values=True).get("skill", [])
            if skills:
                prefix = "" if path == "/" else "/en"
                slug = skills[0]
                if len(skills) == 1 and SLUG.fullmatch(slug):
                    detail = Path(self.directory) / prefix.lstrip("/") / "skills" / slug / "index.html"
                    if detail.is_file():
                        self.send_response(HTTPStatus.FOUND)
                        self.send_header("Location", f"{prefix}/skills/{slug}/")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return None
                return self.missing(path)
        if not PUBLIC_PATH.fullmatch(path):
            return self.missing(path)
        requested = Path(self.directory) / path.strip("/")
        if requested.is_dir():
            requested /= "index.html"
        if not requested.is_file():
            return self.missing(path)
        return super().send_head()

    def log_request(self, code="-", size="-"):
        # Avoid logging arbitrary public request paths and query strings.
        pass

    def send_response(self, code, message=None):
        super().send_response(code, message)
        path = self.path.partition("?")[0]
        if code == HTTPStatus.OK and path.startswith("/downloads/") and PUBLIC_PATH.fullmatch(path):
            self.send_header("Content-Disposition", f'attachment; filename="{path.rsplit("/", 1)[-1]}"')

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        super().end_headers()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--port", default=8766, type=int)
    args = parser.parse_args()
    if not (args.directory / "index.html").is_file():
        parser.error("directory must contain a built registry")
    handler = partial(RegistryHandler, directory=str(args.directory.absolute()))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()
