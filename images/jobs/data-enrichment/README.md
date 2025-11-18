# 📄 Text Embedding and BigQuery Loader

This application processes **drafts** and **pages** data by normalizing text, creating embeddings using OpenAI, and loading the enriched data into **Google BigQuery**.

## ⚙️ Overview

- Retrieves drafts and pages data from source BigQuery tables
- Normalizes text fields (`content` for drafts, `bodytext` for pages)
- Creates vector embeddings using OpenAI’s `text-embedding-3-small` model in batches
- Writes enriched data with embeddings into separate BigQuery target tables for drafts and pages

## 🚀 Deployment

- Packaged as a **Docker container**
- Runs as a standalone Python application (`main.py`)
- Uses Google BigQuery client and OpenAI API for data processing

## 🟢 Trigger

- Triggered weekly on **Mondays at 7 AM** via **Cloud Scheduler**
- Cloud Scheduler trigger is configured **Terraform**.

## 🔧 Environment Variables

Set these environment variables before running:

- `OPENAI_API_KEY`: OpenAI API key for embedding service

## ⚙️ Batch Processing

- Embeddings are created in batches of 200 documents to respect OpenAI token limits
- Each batch is uploaded incrementally to BigQuery to avoid large payloads
