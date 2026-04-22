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

variable "email_provider" {
  type        = string
  default     = "resend"
  description = "EMAIL_PROVIDER for the api ('resend' or 'console')."
}

variable "email_from" {
  type        = string
  default     = "UnderwriteAI <onboarding@resend.dev>"
  description = "EMAIL_FROM header for outbound mail. Resend's onboarding sender works for demos without DMARC setup."
}

variable "email_reply_to" {
  type        = string
  default     = "underwriting@underwriteai.rw"
  description = "EMAIL_REPLY_TO header for outbound mail."
}

variable "email_override_to" {
  type        = string
  default     = ""
  description = "If set, every outbound email is rerouted here. Useful for demos so all mail lands in one inbox."
}

variable "insurer_name" {
  type        = string
  default     = "UnderwriteAI Demo Insurer"
  description = "Insurer name used in email body and decision letters."
}

variable "labels" {
  type = map(string)
  default = {
    project     = "underwrite-ai"
    cost-center = "education"
  }
  description = "Labels attached to every resource for cost tracking."
}
