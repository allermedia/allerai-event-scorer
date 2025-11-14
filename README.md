# Editorial AI Data Platform

This project defines data integrations for the **Editorial AI** team, targeting the **Editorial AI Platform**.

It uses Terraform to manage and provision resources, ensuring consistent and reproducible deployments.

It is designed as a central hub for multiple integrations, each with its own pipelines, ML models, and deployment configuration.

Therefore the repo is **organized by services**, not by integrations:

- **`images/`**: Cloud Run services and jobs
- **`terraform/`**: Infrastructure
- **`docs/`**: Integration-specific documentation

---

## Integrations

This repo contains multiple integrations, which are explained in separate documentation files. Click the docs link to read more.

| Integration           | Description                                                                                                                       | Docs Link                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Page Scoring**      | A two-part pipeline that ingests events, enriches them, and calculates relevance scores and traffic estimates for downstream use. | [Page Scoring Docs](docs/page_scoring.md)           |
| **Platform Matching** | Manages page drafts and published pages, along with a matching system to link published pages to drafts.                          | [Platform Matching Docs](docs/platform_matching.md) |
| **Pageview exporter** | Exports pageviews from all brandsites to the editorial platform.                                                                  | [Pageview exporter](docs/pageview_exporter.md)      |

---
