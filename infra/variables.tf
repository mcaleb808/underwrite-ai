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
  description = "Initial image tag. After first apply, CI overrides the running image and terraform ignores the field."
}

variable "bootstrap_image" {
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
  description = "Placeholder image used to create the Cloud Run service before any real image exists in Artifact Registry. CI replaces it on the first push to main."
}

variable "web_origin" {
  type        = string
  description = "Origin allowed by the api's CORS middleware. Set to the Vercel URL once the frontend is deployed."
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
