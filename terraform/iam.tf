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
}
