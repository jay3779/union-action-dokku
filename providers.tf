terraform {
  required_version = ">= 1.0"
  
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  # Uncomment and configure the backend for remote state management
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "digitalocean/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "digitalocean" {
  token = var.do_token
  # Optional: Set spaces_access_id and spaces_secret_key for S3-compatible storage
  # spaces_access_id = var.do_spaces_access_id
  # spaces_secret_key = var.do_spaces_secret_key
}
