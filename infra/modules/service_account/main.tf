resource "google_service_account" "this" {
  project      = var.project_id
  account_id   = var.account_id
  display_name = "Cloud Run runtime SA for ${var.account_id}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.this.email}"
}

resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.this.email}"
}
