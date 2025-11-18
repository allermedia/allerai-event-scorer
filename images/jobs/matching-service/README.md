# 📄 Article Performance Prediction and BigQuery Integration

This application processes **page/draft embeddings** to find pages origining from drafts using cosine similarity and weighted averages. It integrates with **Google BigQuery** for data retrieval and storage.

## ⚙️ Overview

- Retrieves page/draft data and embeddings from BigQuery
- Identifies candidates using hard filters such as site, creator and publish time limitations
- Calculates cosine similarity between page and draft embeddings to find matches
- Loads prediction results back into BigQuery for reporting or downstream use

## 🚀 Deployment

- Container is deployed to cloud run as a job
- Deployment specifications are configured in **Terraform**

## 🟢 Trigger

- Triggered weekly on **Mondays at 8 AM** via **Cloud Scheduler**
- Cloud Scheduler trigger is configured **Terraform**.

## ⚙️ CLI Backfill Support

This application supports CLI arguments for **manual backfill**. You can specify a custom date range using args:

- --from_date YYYY-MM-DD
- --to_date YYYY-MM-DD

CLI arguments should be set individually with each argument having its own --args flag fx:

- `--args=--from_date=2025-01-01 --args=--to_date=2025-02-01`

CLI arguments are appended as dockerfile sets entrypoint.

Draft from_date is derived from --from_date (set to 14 days before)
