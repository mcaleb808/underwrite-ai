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
  type    = string
  default = "*"
}

variable "labels" { type = map(string) }
