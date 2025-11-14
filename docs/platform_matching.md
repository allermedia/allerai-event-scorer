## 📄 Aller AI Platform Matching

This repository contains data pipelines and supporting code for managing page drafts and published pages, along with a matching system to link published pages to drafts.

### Repository Structure

- **`images/jobs/draft-fetcher`**  
  Pipeline for fetching article drafts from the AI platform. This pipeline extracts draft data and loads it into **Bigquery**.

- **`images/jobs/page-fetcher`**  
  Pipeline for fetching published pages from various brand sites. This pipeline extracts published pages and loads it into **Bigquery**.

- **`images/jobs/pageview-fetcher`**  
  Pipeline for fetching pageviews from pages from various brand sites. This pipeline extracts pageviews and loads it into **Bigquery**.

- **`images/jobs/data-enrichment`**  
  Pipeline for vectorizing pages and drafts. This pipeline extracts published pages and drafts and enriches them, then loads it into **Bigquery**.

- **`images/jobs/matching-service`**  
  Python code for matching published pages with drafts.

### Deployment

All pipelines are containerized using Docker and deployed on Google Cloud Run. The deployment and configuration details are managed via GitHub Actions workflows, defined in the repository’s `.github/workflows/` directory.

---

### Getting Started

1. **Docker & Cloud Run**  
   Build and deploy containers using the provided GitHub workflows or manually via Docker and `gcloud` CLI.

2. **Configuration**  
   Deployment settings and environment variables are configured in GitHub workflow YAML files.
   Variables are stored as github secrets.

---

### Additional Information

- The pipelines leverage the [dlt](https://dlt.dev/) framework for efficient and incremental data loading.
- The matching code helps maintain consistency between draft content and live published pages for better editorial workflow insights.

### 🗺️ Application Flow

Here is a visual overview of the application's workflow:

[![Application Flow](../application_flow.png)](https://miro.com/app/board/uXjVIl8bjrA=/?share_link_id=847040207386)

_Click the image to open the full interactive Miro board._
