resource "google_cloud_run_v2_service" "this" {
  project  = var.project_id
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  labels   = var.labels

  template {
    service_account = var.runtime_sa_email
    timeout         = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.image

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "sqlite+aiosqlite:////tmp/app.db"
      }
      env {
        name  = "CHROMA_DIR"
        value = "/tmp/chroma"
      }
      env {
        name  = "UPLOAD_DIR"
        value = "/tmp/uploads"
      }
      env {
        name  = "WEB_ORIGIN"
        value = var.web_origin
      }
      env {
        name  = "EMAIL_PROVIDER"
        value = "console"
      }

      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.this.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
