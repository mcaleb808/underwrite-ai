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

variable "email_provider" {
  type        = string
  description = "EMAIL_PROVIDER for the api ('resend' or 'console')."
}

variable "email_from" {
  type        = string
  description = "EMAIL_FROM header for outbound mail."
}

variable "email_reply_to" {
  type        = string
  description = "EMAIL_REPLY_TO header for outbound mail."
}

variable "email_override_to" {
  type        = string
  description = "If set, every outbound email is rerouted here."
}

variable "insurer_name" {
  type        = string
  description = "Insurer name used in email body and decision letters."
}

variable "langfuse_public_key" {
  type        = string
  description = "Langfuse public key. Blank disables Langfuse tracing."
}

variable "langfuse_host" {
  type        = string
  description = "Langfuse host URL."
}

variable "labels" { type = map(string) }
