# i™ Counterfactual Data Organism (CDO)

**Research prototype, not a production AI platform or proven novel invention.** This repository implements a deterministic counterfactual dependency graph for numeric source data and a limited two-input arithmetic DSL. It identifies transitively affected nodes, previews value changes, hashes graph states, and requires an explicit version-checked apply. It does not train an AI model, infer dependencies from prose, verify external evidence authenticity, or repair arbitrary code.

## Architecture

`cdo_core/engine.py`: immutable cell records, evidence references, dependency graph, deterministic recomputation, minimal changed-value revisions, optimistic-version conflict checks, SHA-256 snapshot hashes. `cdo_api/server.py`: standard-library loopback-only demonstration JSON HTTP service. `sdk/cdo_client.py`: separately Apache-2.0-licensed Python HTTP client. `tests/`: standard-library unit tests. `legal/`: **non-operative** commercial licensing proposal.

## Run locally (Python 3.10+; no pip dependencies)

```powershell
# From the repository root in PowerShell:
python -m unittest discover -s tests -v
python -m cdo_api.server
```

In another PowerShell window:

```powershell
@'
from sdk.cdo_client import CDOClient
c = CDOClient()
print(c.health())
c.add_source('temperature', 65, 'sensor:1')
c.add_source('offset', 10, 'calibration:1')
c.add_derived('adjusted', ['temperature','offset'], 'add')
preview = c.preview('temperature', 85, 'sensor:2')
print('Preview:', preview)
print('Applied:', c.apply(preview))
'@ | python -
```

`POST /v1/cells` inserts a source cell (`id`, `value`, optional `evidence`) or derived cell (`id`, `dependencies`, `operation`). Supported operations: `add`, `sub`, `mul`, `div`, `min`, `max`; exactly two dependencies. `GET /v1/cells` gives the snapshot; `POST /v1/repairs/preview` takes `id`, `value`, `evidence`; `POST /v1/repairs/apply` additionally requires `base_version`, `before_hash`, and `after_hash` from the preview. `GET /health` reports local-demo status. API state is in-memory and lost on shutdown.

## Engineering boundaries

Evidence is a caller-provided reference, not independently verified. SHA-256 hashes detect accidental differences but are **not** signatures or proof of external truth. The dependency graph is constructed explicitly in insertion order and cannot contain forward references. The API has no authentication, persistence, rate limiting, or public TLS; it deliberately binds only to `127.0.0.1`. Do not expose it through a reverse proxy or deploy it as an internet service. Repair does not automatically modify external files or systems. The prototype must pass tests and independent review before claims of correctness or efficiency.

## Licensing and IP

The **core is currently all-rights-reserved / no general use license** (`LICENSE`); public GitHub view/fork rights still apply. Only `sdk/` carries Apache License 2.0 (`sdk/LICENSE`), which does not license the core or trademarks. `legal/LICENSING-PROPOSAL.md` is a non-operative draft for counsel, not an enacted revenue-threshold license. Do not call this project open source or BSL 1.1. Confirm the legal rights holder and obtain patent/trademark/licensing review before publication or commercial offers.

No telemetry, hidden commercial enforcement, remote licensing calls, model-weight downloads, or destructive lockouts are included.
