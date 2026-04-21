variable "project_id" {
  type        = string
  description = "GCP project hosting the api."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region for Cloud Run + Artifact Registry."
}

variable "env_name" {
  type        = string
  default     = "demo"
  description = "Suffix used to keep resource names unique within the project."
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Tag of the api image to deploy. CI overrides with the git sha."
}

variable "github_owner" {
  type        = string
  description = "GitHub owner/org that holds the deploy workflow."
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name (without owner)."
}

variable "labels" {
  type = map(string)
  default = {
    project     = "underwrite-ai"
    cost-center = "education"
  }
  description = "Labels attached to every resource for cost tracking."
}
