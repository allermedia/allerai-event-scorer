locals {
  topics        = yamldecode(file("${path.module}/config/pubsub/topics.yml"))
  subscriptions = yamldecode(file("${path.module}/config/pubsub/subscriptions.yml"))
}

resource "google_pubsub_topic" "topics" {
  for_each = { for t in local.topics : t.name => t }
  name     = each.value.name
}

resource "google_pubsub_topic" "deadletters" {
  for_each = {
    for s in local.subscriptions : s.name => s
    if contains(keys(s), "deadletter_topic")
  }
  name = each.value.deadletter_topic
}

resource "google_pubsub_subscription" "subscriptions" {
  for_each = { for s in local.subscriptions : s.name => s }

  name  = each.value.name
  topic = google_pubsub_topic.topics[each.value.topic].id

  dynamic "push_config" {
    for_each = contains(keys(each.value), "push_endpoint") ? [1] : []
    content {
      push_endpoint = each.value.push_endpoint
      oidc_token {
        service_account_email = "aller-ai-pubsub-sa@aller-content-tool.iam.gserviceaccount.com"
      }
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

  ack_deadline_seconds = 60

  depends_on = [
    google_bigquery_dataset_iam_member.pubsub_bigquery_access,
    google_service_account_iam_member.allow_pubsub_to_impersonate_pubsub_sa,
    google_service_account_iam_member.allow_terraform_actas_pubsub_sa
  ]
  
  dynamic "dead_letter_policy" {
    for_each = contains(keys(each.value), "deadletter_topic") ? [1] : []
    content {
      dead_letter_topic     = google_pubsub_topic.deadletters[each.key].id
      max_delivery_attempts = 5
    }
  }
}

resource "google_pubsub_subscription" "deadletter_bq_subscriptions" {
  for_each = google_pubsub_topic.deadletters

  name  = "${each.key}-bq-subscription"
  topic = each.value.id

  bigquery_config {
    table = format(
      "%s.%s.%s",
      var.project_id,
      "pubsub_events",
      "${each.key}_dlt_messages"      
    )
    use_topic_schema = false
    write_metadata   = true
  }

  ack_deadline_seconds = 60

  depends_on = [
    google_bigquery_dataset_iam_member.pubsub_bigquery_access
  ]
}