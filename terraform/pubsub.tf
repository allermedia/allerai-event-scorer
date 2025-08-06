locals {
  topics        = yamldecode(file("${path.module}/config/pubsub/topics.yml"))
  subscriptions = yamldecode(file("${path.module}/config/pubsub/subscriptions.yml"))
}

resource "google_pubsub_topic" "topics" {
  for_each = { for t in local.topics : t.name => t }
  name     = each.value.name
}

resource "google_pubsub_subscription" "subscriptions" {
  for_each = { for s in local.subscriptions : s.name => s }

  name  = each.value.name
  topic = google_pubsub_topic.topics[each.value.topic].id

  dynamic "push_config" {
    for_each = contains(keys(each.value), "push_endpoint") ? [1] : []
    content {
      push_endpoint = each.value.push_endpoint
    }
  }

  dynamic "bigquery_config" {
    for_each = contains(keys(each.value), "bigquery_table") ? [1] : []
    content {
      table = format(
        "%s.%s.%s",
        var.project_id,
        split(".", each.value.bigquery_table)[0],
        google_bigquery_table.tables[each.value.bigquery_table].table_id
      )

      use_topic_schema = false
      write_metadata   = true
    }
  }

  ack_deadline_seconds = 10

  depends_on = [
    google_bigquery_dataset_iam_member.pubsub_bigquery_access
  ]
}
