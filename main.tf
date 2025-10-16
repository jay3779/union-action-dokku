# Data source for available SSH keys in DigitalOcean account
data "digitalocean_ssh_keys" "available" {
  sort {
    key       = "created_at"
    direction = "desc"
  }
}

# VPC for grouping resources (optional but recommended)
resource "digitalocean_vpc" "main" {
  name        = "${var.project_name}-vpc-${var.environment}"
  region      = var.region
  description = "VPC for ${var.project_name} - ${var.environment}"
}

# Create droplets from the droplets variable map
resource "digitalocean_droplet" "web" {
  for_each = var.droplets

  name               = "${var.project_name}-${each.value.name}-${var.environment}"
  region             = var.region
  image              = each.value.image
  size               = each.value.size
  backups            = var.enable_backups || each.value.backups
  monitoring         = var.enable_monitoring || each.value.monitoring
  ipv6               = each.value.ipv6
  vpc_uuid           = digitalocean_vpc.main.id
  
  # Add SSH keys if provided
  ssh_keys = length(var.ssh_keys) > 0 ? [
    for key_name in var.ssh_keys : [
      for key in data.digitalocean_ssh_keys.available.keys : key.id
      if key.name == key_name
    ][0]
  ] : []

  # Combine tags
  tags = concat(
    var.common_tags,
    each.value.tags,
    ["${var.environment}-environment"]
  )

  # Graceful shutdown
  graceful_shutdown = true

  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      ssh_keys  # Prevent Terraform from overwriting manually added keys
    ]
  }
}

# Optional: Create a firewall for additional security
resource "digitalocean_firewall" "web" {
  name        = "${var.project_name}-firewall-${var.environment}"
  description = "Firewall for ${var.project_name} web servers"

  # Inbound rules
  inbound_rule {
    protocol    = "tcp"
    port_range  = "22"
    source_type = "app"
  }

  inbound_rule {
    protocol    = "tcp"
    port_range  = "80"
    source_type = "app"
  }

  inbound_rule {
    protocol    = "tcp"
    port_range  = "443"
    source_type = "app"
  }

  inbound_rule {
    protocol    = "icmp"
    source_type = "app"
  }

  # Outbound rules - allow all
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1"
    destination_type      = "cidr"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1"
    destination_type      = "cidr"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_type      = "cidr"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  tags = var.common_tags
}

# Attach firewall to droplets
resource "digitalocean_firewall_droplets" "web" {
  firewall_id = digitalocean_firewall.web.id

  droplet_ids = [
    for droplet in digitalocean_droplet.web : droplet.id
  ]
}
