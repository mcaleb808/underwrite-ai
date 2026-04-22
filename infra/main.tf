locals {
  name_suffix = var.env_name
  labels = merge(var.labels, {
    env = var.env_name
  })
}

resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

module "artifact_registry" {
  source     = "./modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
  name       = "underwrite-${local.name_suffix}"
  labels     = local.labels

  depends_on = [google_project_service.apis]
}

module "service_account" {
  source     = "./modules/service_account"
  project_id = var.project_id
  account_id = "underwrite-api-${local.name_suffix}"

  depends_on = [google_project_service.apis]
}

module "secrets" {
  source           = "./modules/secrets"
  project_id       = var.project_id
  runtime_sa_email = module.service_account.email
  secret_ids = [
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "RESEND_API_KEY",
  ]
  name_suffix = local.name_suffix
  labels      = local.labels

  depends_on = [google_project_service.apis]
}

module "cloud_run" {
  source            = "./modules/cloud_run"
  project_id        = var.project_id
  region            = var.region
  service_name      = "underwrite-api-${local.name_suffix}"
  image             = var.bootstrap_image
  runtime_sa_email  = module.service_account.email
  secret_env        = module.secrets.env_bindings
  web_origin        = var.web_origin
  email_provider    = var.email_provider
  email_from        = var.email_from
  email_reply_to    = var.email_reply_to
  email_override_to = var.email_override_to
  insurer_name      = var.insurer_name
  labels            = local.labels

  depends_on = [module.artifact_registry, module.secrets]
}

module "wif" {
  source           = "./modules/wif"
  project_id       = var.project_id
  pool_id          = "github-${local.name_suffix}"
  github_owner     = var.github_owner
  github_repo      = var.github_repo
  artifact_repo_id = module.artifact_registry.repository_id
  region           = var.region
  cloud_run_name   = module.cloud_run.service_name
  runtime_sa_email = module.service_account.email
  deploy_sa_id     = "underwrite-deploy-${local.name_suffix}"

  depends_on = [google_project_service.apis]
}
