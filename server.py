"""Minimal read-only HTTP server for the APRS weather map.

Only the frontend and explicitly selected generated data are public.
No repository files, secrets, archives or Python sources are served.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import mimetypes

ROOT = Path(__file__).resolve().parent
WEB = (ROOT / "web").resolve()
DATA = (ROOT / "data").resolve()
DATA_FILES = {
    "/data/latest.json": DATA / "latest.json",
    "/data/temperature.geojson": DATA / "temperature.geojson",
    "/data/pressure.geojson": DATA / "pressure.geojson",
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ("/", "/web"):
            self.send_response(302)
            self.send_header("Location", "/web/")
            self.end_headers()
            return
        if path in DATA_FILES:
            target = DATA_FILES[path]
        elif path.startswith("/web/data/") and path[len("/web"):] in DATA_FILES:
            target = DATA_FILES[path[len("/web"):]]
        elif path == "/web/":
            target = WEB / "index.html"
        elif path.startswith("/web/"):
            target = (WEB / path[len("/web/"):]).resolve()
            if not target.is_relative_to(WEB):
                self.send_error(403, "Forbidden")
                return
        else:
            self.send_error(404, "Not found")
            return
        if not target.is_file():
            self.send_error(404, "Not found")
            return
        # Reject symlinks pointing outside the allowed frontend directory.
        if path.startswith("/web/") and not target.resolve().is_relative_to(WEB):
            self.send_error(403, "Forbidden")
            return
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix == ".geojson":
            mime = "application/geo+json"
        try:
            with target.open("rb") as file:
                self.send_response(200)
                self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") or "json" in mime else ""))
                self.send_header("Content-Length", str(target.stat().st_size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                while chunk := file.read(65536):
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_HEAD(self):
        self.send_error(405, "Method not allowed")

def main():
    parser = argparse.ArgumentParser(description="Serve APRS Weather Map locally")
    parser.add_argument("--host", default="127.0.0.1", help="Default: localhost only")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"APRS Weather Map: http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
