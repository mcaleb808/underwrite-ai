output "deploy_sa_email" {
  value = google_service_account.deploy.email
}

output "provider_name" {
  value = google_iam_workload_identity_pool_provider.github.name
}
