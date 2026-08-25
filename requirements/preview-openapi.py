"""Serve Swagger UI and ReDoc for requirements/openapi.yaml."""
from __future__ import annotations

import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

SPEC = Path(__file__).with_name("openapi.yaml")
SWAGGER_PORT = 8080
REDOC_PORT = 8081

SWAGGER_HTML = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sea Battle API - Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function () {
      window.ui = SwaggerUIBundle({
        url: "/openapi.yaml",
        dom_id: "#swagger-ui",
        presets: [SwaggerUIBundle.presets.apis],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>
"""

REDOC_HTML = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Sea Battle API - ReDoc</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
  <redoc spec-url="/openapi.yaml"></redoc>
  <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


def make_handler(index_html: bytes):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                body, ctype = index_html, "text/html; charset=utf-8"
            elif path in ("/openapi.yaml", "/openapi.yml"):
                body, ctype = SPEC.read_bytes(), "application/yaml; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            print("[%s] %s" % (self.address_string(), fmt % args))

    return Handler


def first_free_port(preferred: int) -> int:
    port = preferred
    while port < preferred + 20:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("No free port near %s" % preferred)


def serve(port: int, html: bytes) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(html))
    print("listening on http://127.0.0.1:%s" % port, flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    if not SPEC.is_file():
        raise SystemExit("openapi.yaml not found next to this script")
    swagger_port = first_free_port(SWAGGER_PORT)
    redoc_port = first_free_port(REDOC_PORT if swagger_port != REDOC_PORT else REDOC_PORT + 1)
    if redoc_port == swagger_port:
        redoc_port = first_free_port(swagger_port + 1)
    print("Swagger UI: http://127.0.0.1:%s/" % swagger_port, flush=True)
    print("ReDoc:      http://127.0.0.1:%s/" % redoc_port, flush=True)
    print("Open these URLs in Chrome or Edge, not Cursor Simple Browser.", flush=True)
    Thread(target=serve, args=(swagger_port, SWAGGER_HTML), daemon=True).start()
    serve(redoc_port, REDOC_HTML)
