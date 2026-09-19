# i™ CDO licensing proposal — NON-OPERATIVE DRAFT

**This document grants no permissions and is not an offer, executed agreement, or legal advice.** Counsel and the verified copyright owner must approve and publish operative license terms. Current rights are described in the root `LICENSE` and `sdk/LICENSE`.

## Intended commercial model

- Core (`cdo_core/`, `cdo_api/`): source-available; all rights reserved pending an operative core license. Publication on GitHub does not automatically grant commercial or modification rights; GitHub's view/fork terms still apply.
- Standalone SDK (`sdk/`): Apache-2.0. SDK users do not thereby receive a license to the core or to the i™ trademarks.
- Proposed community core grant: permit evaluation, research and limited production for qualifying persons/entities; define eligibility using measurable aggregate annual gross revenue and controlled affiliates, with a specific USD threshold and a clear measurement period. Specify use limitations, modifications, distribution, network use, reporting, support and termination in an attorney-approved instrument.
- Proposed paid enterprise agreement: explicitly define production use, deployment scale, private modifications, redistribution, proprietary hosting, commercial fees, audit scope, support and separately negotiated warranties or indemnities. No warranty or indemnity is promised by this draft.
- Contributions: obtain separately signed contributor terms where necessary; do not assume a pull request transfers copyright or patent ownership. Make the inbound/outbound licensing relationship explicit.

## Why not call a custom text BSL 1.1?

The official Business Source License 1.1 is source-available and has a mandatory change to an open-source license by the applicable change date (at most four years after a version's first public distribution). Its official text cannot simply be modified at will while retaining the BSL name. Requiring all modifications to be assigned or contributed back is **not** a standard BSL 1.1 term. A custom license with mandatory contribution-back, a revenue threshold and restricted forks requires dedicated legal drafting. Refer to https://mariadb.com/bsl11/ .

## Patent, brand, privacy and claims checklist

1. Confirm who legally owns the code and any relevant rights. `AdvanceDisrto` is a repository account name, **not** proof of legal entity ownership. Verify whether iNNOVULIS is the legal licensor before publishing operative legal documents.
2. Before disclosing potentially patentable mechanisms publicly, request qualified patent counsel review of filing and publication strategy, including any applicable grace-period and foreign-rights issues. This repository contains a limited prototype; its publication does not prove invention, novelty, priority, or patent coverage.
3. Verify trademark ownership, registration status and approved uses of i™, iNNOVULIS, and other marks. A copyright license alone does not grant a trademark registration.
4. Avoid collecting revenue, employee counts, personal data, or deployment telemetry by default. Require informed disclosure and appropriate privacy/security assessment before adding remote license reporting.
5. Define thresholds and affiliates unambiguously, provide accessible license terms before any enforcement, and avoid destructive software lockouts or unannounced shutdowns.
6. Obtain legal review of governing law, export restrictions, third-party license compatibility, consumer protections, liability, privacy, and actual enforceability.

## Sources

- Official BSL 1.1: https://mariadb.com/bsl11/
- GitHub guidance on no-license defaults and public repository view/fork rights: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0
