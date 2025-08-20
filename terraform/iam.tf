data "google_project" "project" {}

resource "google_bigquery_dataset_iam_member" "pubsub_bigquery_access" {
  for_each = {
    for s in local.subscriptions :
    s.name => s
    if contains(keys(s), "bigquery_table")
  }

  dataset_id = split(".", each.value.bigquery_table)[0]
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

  depends_on = [google_bigquery_dataset.datasets]
}

resource "google_cloud_run_service_iam_member" "allow_pubsub_push" {
  for_each = { for svc in local.cloudrun_services : svc.name => svc }

  service  = each.value.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "allow_pubsub_to_impersonate_pubsub_sa" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "allow_terraform_actas_pubsub_sa" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:aller-ai-sa@aller-content-tool.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dlt_publisher" {
  for_each = google_pubsub_topic.deadletters

  topic  = each.value.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
}

resource "google_pubsub_topic_iam_member" "dlt_subscriber" {
  for_each = google_pubsub_topic.deadletters

  topic  = each.value.id
  role   = "roles/pubsub.subscriber"
  member = "serviceAccount:aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
}
