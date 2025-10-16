output "id" {
  description = "Droplet ID"
  value       = digitalocean_droplet.droplet.id
}

output "ipv4_address" {
  description = "IPv4 address"
  value       = digitalocean_droplet.droplet.ipv4_address
}

output "ipv6_address" {
  description = "IPv6 address"
  value       = try(digitalocean_droplet.droplet.ipv6_address, null)
}

output "ipv4_address_private" {
  description = "Private IPv4 address"
  value       = try(digitalocean_droplet.droplet.ipv4_address_private, null)
}

output "status" {
  description = "Droplet status"
  value       = digitalocean_droplet.droplet.status
}

output "created_at" {
  description = "Creation timestamp"
  value       = digitalocean_droplet.droplet.created_at
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh root@${digitalocean_droplet.droplet.ipv4_address}"
}
