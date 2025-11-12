locals {
  cloud_run_job_triggers      = yamldecode(file("${path.module}/config/cloud_scheduler/cloud_run_job_triggers.yml"))
}

resource "google_cloud_scheduler_job" "cloud_run_jobs" {
  project = var.project_id

  for_each = local.cloud_run_job_triggers

  name        = each.key
  description = each.value.description

  region = "europe-central2"

  schedule         = each.value.schedule
  time_zone        = try(each.value.time_zone, "Europe/Copenhagen")
  attempt_deadline = try(each.value.attempt_deadline, "300s")

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${google_cloud_run_v2_job.jobs[each.value.job_name].location}/jobs/${google_cloud_run_v2_job.jobs[each.value.job_name].name}:run"
    oauth_token {
      service_account_email = google_service_account.service_accounts["cloud-run-invoker"].email
    }
  }

}
