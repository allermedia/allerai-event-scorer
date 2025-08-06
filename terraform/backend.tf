terraform {
  backend "gcs" {
    bucket  = "allerai-event-scorer-terraform-state-bucket"
    prefix  = "envs/prod"
  }
}
