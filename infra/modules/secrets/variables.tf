variable "project_id" { type = string }
variable "secret_ids" { type = list(string) }
variable "runtime_sa_email" { type = string }
variable "name_suffix" { type = string }
variable "labels" { type = map(string) }
