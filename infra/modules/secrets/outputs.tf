output "env_bindings" {
  value = {
    for raw_id, secret in google_secret_manager_secret.this :
    raw_id => secret.secret_id
  }
  description = "Map of env-var name -> secret_manager secret_id (suffixed)."
}
