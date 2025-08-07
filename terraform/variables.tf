variable "project_id" {
  default = "aller-content-tool"
}
variable "region" {
  default = "europe-north2"
}
variable "image_url" {
  description = "Deployed Cloud Run image URL"
  default = "europe-docker.pkg.dev" 
}
variable "env_vars" {
  description = "Environment variables for the Cloud Run service"
  type        = map(string)
}
