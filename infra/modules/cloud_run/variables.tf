variable "project_id" { type = string }
variable "region" { type = string }
variable "service_name" { type = string }
variable "image" { type = string }
variable "runtime_sa_email" { type = string }

variable "secret_env" {
  type        = map(string)
  description = "Map of env-var name -> Secret Manager secret_id."
}

variable "web_origin" {
  type        = string
  description = "Origin allowed by the api's CORS middleware. Set to the Vercel URL."
}

variable "max_instances" {
  type        = number
  default     = 1
  description = "Cloud Run max instance count. Defaults to 1 so per-instance sqlite stays consistent."
}

variable "labels" { type = map(string) }
