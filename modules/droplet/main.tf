resource "digitalocean_droplet" "droplet" {
  name               = var.name
  region             = var.region
  image              = var.image
  size               = var.size
  ssh_keys           = var.ssh_keys
  backups            = var.backups
  monitoring         = var.monitoring
  ipv6               = var.ipv6
  vpc_uuid           = var.vpc_uuid
  tags               = var.tags
  user_data          = var.user_data
  graceful_shutdown  = true

  lifecycle {
    create_before_destroy = true
  }
}
