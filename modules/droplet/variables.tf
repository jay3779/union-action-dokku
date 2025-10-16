variable "name" {
  description = "Name of the droplet"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
}

variable "image" {
  description = "Image slug for the droplet"
  type        = string
}

variable "size" {
  description = "Droplet size slug"
  type        = string
}

variable "ssh_keys" {
  description = "List of SSH key IDs"
  type        = list(string)
  default     = []
}

variable "backups" {
  description = "Enable backups"
  type        = bool
  default     = false
}

variable "monitoring" {
  description = "Enable monitoring"
  type        = bool
  default     = false
}

variable "ipv6" {
  description = "Enable IPv6"
  type        = bool
  default     = true
}

variable "vpc_uuid" {
  description = "VPC UUID"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags for the droplet"
  type        = list(string)
  default     = []
}

variable "user_data" {
  description = "User data script"
  type        = string
  default     = null
}
