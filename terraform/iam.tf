locals {
  subscription_datasets = {
    for s in local.subscriptions :
    s.name => split(".", try(s.bigquery_table, ""))[0]
    if contains(keys(s), "bigquery_table")
  }
}

data "google_project" "project" {}

resource "google_bigquery_dataset_iam_member" "pubsub_bigquery_access" {
  for_each = {
    for s in local.subscriptions :
    s.name => s
    if contains(keys(s), "bigquery_table")
  }

  dataset_id = local.subscription_datasets[each.key]
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"

  depends_on = [
    google_bigquery_dataset.datasets[local.subscription_datasets[each.key]]
  ]
}
