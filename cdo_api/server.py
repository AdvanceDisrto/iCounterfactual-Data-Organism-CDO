"""Local-only JSON API; NOT a public production service.

Run: python -m cdo_api.server. No arbitrary code execution, no background jobs.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from cdo_core import CDO, ConflictError

engine = CDO()


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.respond(200, {"status": "ok", "mode": "local-demo"})
        elif self.path == "/v1/cells":
            self.respond(200, engine.snapshot())
        else:
            self.respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path not in ("/v1/cells", "/v1/repairs/preview", "/v1/repairs/apply"):
            self.respond(404, {"error": "not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536:
                self.respond(413, {"error": "JSON body must be 1..65536 bytes"})
                return
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("expected a JSON object")
            if self.path == "/v1/cells":
                cell = engine.add(data["id"], data.get("value"), evidence=data.get("evidence", ""),
                                  dependencies=data.get("dependencies", []), operation=data.get("operation"))
                self.respond(201, cell.as_dict())
            elif self.path == "/v1/repairs/preview":
                plan = engine.plan(data["id"], data["value"], evidence=data["evidence"])
                self.respond(200, plan.as_dict())
            else:
                # A client supplies the version and expected hashes from its preview.
                plan = engine.plan(data["id"], data["value"], evidence=data["evidence"])
                if (data.get("base_version") != plan.base_version or
                    data.get("before_hash") != plan.before_hash or
                    data.get("after_hash") != plan.after_hash):
                    raise ConflictError("preview/version mismatch: obtain a fresh preview")
                self.respond(200, engine.apply(plan))
        except ConflictError as exc:
            self.respond(409, {"error": str(exc)})
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            self.respond(400, {"error": str(exc)})


def main():
    host = "127.0.0.1"
    port = int(os.environ.get("CDO_PORT", "8765"))
    if not 0 < port < 65536:
        raise ValueError("invalid port")
    print(f"CDO local demo: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
