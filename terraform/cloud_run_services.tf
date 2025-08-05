locals {
  cloudrun = yamldecode(file("${path.module}/config/cloud_run/services.yml"))
  
  cloud_run_service_defaults = {
    image   = null
    command = ["python", "main.py"]
    resources = {
      cpu    = "1"
      memory = "512Mi"
    }
    port = 8080
    scaling = {
      min_instance_count = 0
      max_instance_count = 1
    }
    location        = var.region
    service_account = null
  }

  cloud_run_config = merge(local.cloud_run_service_defaults, local.cloudrun)
}

resource "google_cloud_run_service" "service" {
  name     = local.cloud_run_config.name
  location = local.cloud_run_config.location

  template {
    spec {
      containers {

        image = "${var.image_url}/${var.project_id}/docker/${local.cloud_run_config.image}:latest"

        resources {
          limits = {
            memory = local.cloud_run_config.resources.memory
            cpu    = local.cloud_run_config.resources.cpu
          }
        }

        ports {
          container_port = local.cloud_run_config.port
        }

        command = local.cloud_run_config.command
      }

      service_account_name = local.cloud_run_config.service_account
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}