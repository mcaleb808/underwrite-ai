resource "google_secret_manager_secret" "this" {
  for_each  = toset(var.secret_ids)
  project   = var.project_id
  secret_id = "${each.key}_${var.name_suffix}"
  labels    = var.labels

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "runtime_access" {
  for_each  = google_secret_manager_secret.this
  project   = var.project_id
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_sa_email}"
}
