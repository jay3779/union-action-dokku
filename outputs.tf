output "vpc_id" {
  description = "ID of the VPC"
  value       = digitalocean_vpc.main.id
}

output "vpc_urn" {
  description = "URN of the VPC"
  value       = digitalocean_vpc.main.urn
}

output "droplet_ips" {
  description = "Map of droplet names to their IPv4 addresses"
  value = {
    for key, droplet in digitalocean_droplet.web :
    key => droplet.ipv4_address
  }
}

output "droplet_details" {
  description = "Detailed information about all droplets"
  value = {
    for key, droplet in digitalocean_droplet.web :
    key => {
      id           = droplet.id
      name         = droplet.name
      ipv4_address = droplet.ipv4_address
      ipv6_address = try(droplet.ipv6_address, null)
      region       = droplet.region
      size         = droplet.size
      image        = droplet.image
      status       = droplet.status
      tags         = droplet.tags
      created_at   = droplet.created_at
      memory       = droplet.memory
      vcpus        = droplet.vcpus
    }
  }
}

output "firewall_id" {
  description = "ID of the firewall"
  value       = digitalocean_firewall.web.id
}

output "firewall_urn" {
  description = "URN of the firewall"
  value       = digitalocean_firewall.web.urn
}

output "ssh_command" {
  description = "SSH commands to connect to droplets"
  value = {
    for key, droplet in digitalocean_droplet.web :
    key => "ssh root@${droplet.ipv4_address}"
  }
}
