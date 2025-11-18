# 📄 Aller AI Platform Page Fetcher

This application defines a DLT pipeline that fetches **published pages** from the **Aller Data Platform** and loads them into a **Google BigQuery** target dataset using **Data Load Tool (DLT)**.

## ⚙️ Overview

- Retrieves pages from the BigQuery source table:  
  `editorial.pages`
- Checks existing pages in the target table:  
  `adp_pages.pages`
- Avoids inserting duplicate `page_id`s by:
  - Reading `page_id`s already in the target table within the same date range
  - Filtering them out before yielding new rows to DLT

## 🚀 Deployment

- The application is deployed as a **Cloud Run job**
- Deployment and schedule are configured in **Terraform**

## 🟢 Trigger

- Triggered weekly on **Mondays at 6 AM** via **Cloud Scheduler**
- Cloud Scheduler trigger is configured **Terraform**.

## 🔐 Secret Management

- The reader service account JSON key is stored securely in **Secret Manager**
- Secret Manager key is accessed at runtime to initialize the source BigQuery client

## 🔧 Environment Variables

This application takes the following environment variables (Set a deployment):

- `SECRET_NAME`: The name of the secret in Secret Manager containing the reader SA key

## ⚙️ CLI Backfill Support

This application supports CLI arguments for **manual backfill**. You can specify a custom date range using args:

- --from_date YYYY-MM-DD
- --to_date YYYY-MM-DD

CLI arguments should be set individually with each argument having its own --args flag fx:

- `--args=--from_date=2025-01-01 --args=--to_date=2025-02-01`
  CLI arguments are appended as dockerfile sets entrypoint.
