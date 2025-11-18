# 📄 Aller AI Platform Pageview Fetcher

This application defines a DLT pipeline that fetches **pageviews for published pages** from the **Aller Data Platform** and loads them into a **Google BigQuery** target dataset using **Data Load Tool (DLT)**.

## ⚙️ Overview

- Retrieves pageviews from the BigQuery source table:  
  `editorial.web_traffic_pageviews`
- Aggregates pageviews on dimension event_date, site_domain.
- Checks existing events_date in the target table to avoid duplicate insertions:  
  `adp_pageviews.pages_pageviews`

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

- NOTE: Backfill does not overwrite existing dates, meant for initial runs.
