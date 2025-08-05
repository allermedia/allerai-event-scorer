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

  push_config {
    push_endpoint = each.value.push_endpoint
  }

  ack_deadline_seconds = 10
}
