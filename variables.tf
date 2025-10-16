variable "do_token" {
  description = "DigitalOcean API token for authentication"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region for resources"
  type        = string
  default     = "nyc3"
  
  validation {
    condition     = contains(["nyc1", "nyc3", "sfo1", "sfo2", "sfo3", "lon1", "ams2", "ams3", "fra1", "blr1", "sgp1", "tor1"], var.region)
    error_message = "Region must be a valid DigitalOcean region."
  }
}

variable "project_name" {
  description = "Project name for resource naming and tagging"
  type        = string
  default     = "my-project"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "droplets" {
  description = "Map of droplet configurations"
  type = map(object({
    name         = string
    image        = string
    size         = string
    backups      = optional(bool, false)
    ipv6         = optional(bool, true)
    monitoring   = optional(bool, false)
    vpc_uuid     = optional(string, null)
    tags         = optional(list(string), [])
  }))
  default = {
    web-01 = {
      name   = "web-server-01"
      image  = "ubuntu-24-04-x64"
      size   = "s-1vcpu-1gb"
      tags   = ["web", "production"]
    }
  }
}

variable "ssh_keys" {
  description = "List of SSH key names to add to droplets"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = list(string)
  default     = ["terraform", "managed"]
}

variable "enable_monitoring" {
  description = "Enable DigitalOcean monitoring for droplets"
  type        = bool
  default     = false
}

variable "enable_backups" {
  description = "Enable automatic backups for droplets"
  type        = bool
  default     = false
}
