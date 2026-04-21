output "api_url" {
  value       = module.cloud_run.url
  description = "Public Cloud Run URL of the api."
}

output "artifact_repository" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_id}"
  description = "Docker image path used by the deploy workflow."
}

output "runtime_service_account" {
  value       = module.service_account.email
  description = "Service account the Cloud Run revision runs as."
}

output "deploy_service_account" {
  value       = module.wif.deploy_sa_email
  description = "Service account GitHub Actions impersonates via WIF."
}

output "workload_identity_provider" {
  value       = module.wif.provider_name
  description = "Set as GitHub Actions secret WIF_PROVIDER."
}
