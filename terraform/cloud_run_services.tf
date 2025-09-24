locals {
  cloudrun_services = yamldecode(file("${path.module}/config/cloud_run/services.yml"))

  cloud_run_service_defaults = {
    image   = null
    resources = {
      cpu    = "1"
      memory = "1Gi"
    }
    port = 8080
    scaling = {
      min_instance_count = 0
      max_instance_count = 1
    }
    location        = var.region
    service_account = null
    env_vars        = []
  }

  cloudrun_merged = {
    for service in local.cloudrun_services :
    service.name => merge(local.cloud_run_service_defaults, service)
  }
}

resource "google_cloud_run_service" "service" {
  for_each = local.cloudrun_merged

  name     = each.value.name
  location = each.value.location

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = tostring(each.value.scaling.min_instance_count)
        "autoscaling.knative.dev/maxScale" = tostring(each.value.scaling.max_instance_count)
      }
    }
    spec {
      containers {
        image = "${var.image_url}/${var.project_id}/docker/${each.value.image}:latest"

        resources {
          limits = {
            memory = each.value.resources.memory
            cpu    = each.value.resources.cpu
          }
        }

        ports {
          container_port = try(each.value.port, local.cloud_run_service_defaults.port)
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

      service_account_name = each.value.service_account

    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}