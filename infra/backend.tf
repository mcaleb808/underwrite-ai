terraform {
  backend "gcs" {
    # Bucket + prefix supplied via `terraform init -backend-config=...`
    # See infra/README.md for the bootstrap command.
  }
}
