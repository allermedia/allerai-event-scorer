locals {
  cloudrun_jobs = yamldecode(file("${path.module}/config/cloud_run/jobs.yml"))

  cloud_run_job_defaults = {
    image   = null
    command = ["python", "main.py"]
    resources = {
      cpu    = "1"
      memory = "512Mi"
    }
    location        = "europe-north2"
    task_timeout    = "3600s"
    service_account = null
  }

  cloudrun_jobs_merged = {
    for job in local.cloudrun_jobs :
    job.name => merge(local.cloud_run_job_defaults, job)
  }
}

resource "google_cloud_run_v2_job" "jobs" {
  for_each = local.cloudrun_jobs_merged

  name     = each.value.name
  location = each.value.location

  template {
    template {
      containers {

        image = "europe-docker.pkg.dev/${var.project_id}/docker/${try(each.value.image, each.key)}:latest"

        command = try(each.value.command, local.cloud_run_job_defaults.command)

        resources {
          limits = {
            cpu    = each.value.resources.cpu
            memory = each.value.resources.memory
          }
        }


        dynamic "env" {
          for_each = {
            for k in each.value.env_vars : k => lookup(var.env_vars, k, null)
            if lookup(var.env_vars, k, null) != null
          }

          content {
            name  = env.key
            value = env.value
          }
        }
        
      }

      timeout = each.value.task_timeout
      service_account = each.value.service_account

    }
  }
}