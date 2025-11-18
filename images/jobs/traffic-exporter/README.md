# 📄 Aller AI Platform Traffic Exporter

This pipeline fetches **daily traffic for published pages** as well as **page cms id's** from the **Aller Data Platform** and posts them to the Editorial AI Platform.

## ⚙️ Overview

- Retrieves traffic from the BigQuery source table:  
  `editorial.agg_web_traffic_by_page`
- Retrieves page id's from the BigQuery source table:  
  `editorial.pages`
- Appends cms page id's to the traffic data
- Transforms the traffic data to desired schema
- Posts the traffic data to the Editorial AI Platform

## 🚀 Deployment

- The application is deployed as a **Cloud Run job**
- Deployment and schedule are configured in **Terraform**

## 🟢 Trigger

- Triggered daily at **6 AM** via **Cloud Scheduler**
- Cloud Scheduler trigger is configured **Terraform**

## 🔐 Secret Management

- The Editorial AI Platform endpoint and API key is stored securely in **Github Secrets**

## 🔧 Environment Variables

This application takes the following environment variables (Set a deployment):

- `PLATFORM_API_KEY`: The name of the secret in github secrets containing the API key
- `PLATFORM_TRAFFIC_ENDPOINT`: The endpoint URL for the Editorial AI Platform API
