"""Small standalone CDO HTTP client. Apache-2.0; see sdk/LICENSE.

Copyright 2026 AdvanceDisrto. Licensed under Apache License 2.0.
"""
import json
from urllib.request import Request, urlopen


class CDOClient:
    def __init__(self, base_url="http://127.0.0.1:8765"):
        self.base_url = base_url.rstrip("/")

    def _request(self, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=data,
                          headers={"Content-Type": "application/json"} if data is not None else {},
                          method="POST" if data is not None else "GET")
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read(1_048_576))

    def health(self):
        return self._request("/health")

    def snapshot(self):
        return self._request("/v1/cells")

    def add_source(self, cell_id, value, evidence=""):
        return self._request("/v1/cells", {"id": cell_id, "value": value, "evidence": evidence})

    def add_derived(self, cell_id, dependencies, operation, evidence=""):
        return self._request("/v1/cells", {"id": cell_id, "dependencies": dependencies,
                                           "operation": operation, "evidence": evidence})

    def preview(self, cell_id, value, evidence):
        return self._request("/v1/repairs/preview", {"id": cell_id, "value": value, "evidence": evidence})

    def apply(self, preview):
        return self._request("/v1/repairs/apply", {
            "id": preview["target"], "value": preview["replacement"],
            "evidence": preview["evidence"], "base_version": preview["base_version"],
            "before_hash": preview["before_hash"], "after_hash": preview["after_hash"]})
