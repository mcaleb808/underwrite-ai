data "google_project" "current" {
  project_id = var.project_id
}

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = var.pool_id
  display_name              = "GitHub Actions (${var.pool_id})"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.actor"      = "assertion.actor"
    "attribute.ref"        = "assertion.ref"
  }

  # Repo + branch pin: only workflow runs on the main branch of this exact repo
  # can mint a token for the deploy SA. Feature branches and forks cannot.
  attribute_condition = "attribute.repository == \"${var.github_owner}/${var.github_repo}\" && attribute.ref == \"refs/heads/main\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = var.deploy_sa_id
  display_name = "Deploy SA for GitHub Actions"
}

resource "google_service_account_iam_member" "wif_binding" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_owner}/${var.github_repo}"
}

resource "google_artifact_registry_repository_iam_member" "deploy_writer" {
  project    = var.project_id
  location   = var.region
  repository = var.artifact_repo_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_cloud_run_v2_service_iam_member" "deploy_admin" {
  project  = var.project_id
  location = var.region
  name     = var.cloud_run_name
  role     = "roles/run.admin"
  member   = "serviceAccount:${google_service_account.deploy.email}"
}

resource "google_service_account_iam_member" "deploy_can_act_as_runtime" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.runtime_sa_email}"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deploy.email}"
}
