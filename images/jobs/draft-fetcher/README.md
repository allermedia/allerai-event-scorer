# 📄 Aller AI Platform Draft Fetcher

This application provides a pipeline to fetch draft metadata from a **Mongo DB** collection using the **Data Load Tool (DLT)** and load it into **Google BigQuery**.

## ⚙️ Overview

- Retrieve all drafts from mongodb collection from **Aller AI Platform**
- Retrieve stored drafts from bigquery table:
  `platform_drafts.citation_story_export`
- Identify existing drafts by matching on primary key **\_id**
- Insert new drafts, upsert existing draft if created within last 7 days

## 🚀 Deployment

- Container is deployed to cloud run as a job
- Deployment specifications are configured in **Terraform**

## 🟢 Trigger

- Triggered weekly on **Mondays at 6 AM** via **Cloud Scheduler**
- Cloud Scheduler trigger is configured **Terraform**.
