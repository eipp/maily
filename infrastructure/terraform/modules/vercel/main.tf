# Vercel Project Module

variable "project_name" {
  description = "Name of the Vercel project"
  type        = string
}

variable "framework" {
  description = "Framework used in the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "domain" {
  description = "Domain for the project"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the project"
  type        = map(string)
  default     = {}
}

resource "vercel_project" "app" {
  name      = var.project_name
  framework = var.framework

  git_repository = {
    type = "github"
    repo = "maily/maily"
  }
}

resource "vercel_project_domain" "domain" {
  project_id = vercel_project.app.id
  domain     = var.domain
}

resource "vercel_project_environment_variable" "env_vars" {
  for_each = var.environment_variables

  project_id = vercel_project.app.id
  key        = each.key
  value      = each.value
  target     = [var.environment]
}

output "project_id" {
  value = vercel_project.app.id
}

output "project_url" {
  value = vercel_project.app.url
}