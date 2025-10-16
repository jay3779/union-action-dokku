# Terraform DigitalOcean Infrastructure

Production-ready Terraform configuration for managing DigitalOcean droplets and related infrastructure.

## 📋 Overview

This Terraform configuration enables you to:
- **Deploy and manage DigitalOcean droplets** at scale
- **Organize infrastructure** with VPCs and firewalls
- **Apply consistent naming conventions** across all resources
- **Track infrastructure state** with Terraform
- **Version control infrastructure** with Git
- **Automate deployments** with CI/CD pipelines

## 🚀 Quick Start

### Prerequisites

1. **Terraform** >= 1.0 ([Install Terraform](https://www.terraform.io/downloads))
2. **DigitalOcean Account** with an API token ([Create Token](https://cloud.digitalocean.com/account/api/tokens))
3. **SSH Key** added to DigitalOcean account (optional but recommended)

### Setup Instructions

#### 1. Clone/Initialize the Repository

```bash
# Initialize Terraform in the workspace
terraform init
```

#### 2. Configure Your API Token

You have several options to provide your DigitalOcean API token:

**Option A: Environment Variable (Recommended for security)**
```bash
$env:DIGITALOCEAN_ACCESS_TOKEN = "your_token_here"
# or in PowerShell
$env:DO_PAT = "your_token_here"
```

**Option B: terraform.tfvars File**
```bash
# Copy the example file
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and add your token
# WARNING: Never commit terraform.tfvars to version control!
```

**Option C: Command Line**
```bash
terraform apply -var="do_token=your_token_here"
```

#### 3. Customize Variables

Edit `terraform.tfvars` to customize:
- **Region**: Where your droplets will be created
- **Project Name**: Used for naming convention
- **Environment**: dev, staging, or prod
- **Droplets**: Add/modify droplet configurations
- **SSH Keys**: Names of SSH keys to attach

#### 4. Plan the Deployment

```bash
# Review what Terraform will create
terraform plan -out=tfplan
```

#### 5. Apply the Configuration

```bash
# Create resources on DigitalOcean
terraform apply tfplan
```

#### 6. View Outputs

```bash
# Display important resource information
terraform output

# Get specific output
terraform output droplet_ips
terraform output ssh_command
```

## 📁 Project Structure

```
.
├── providers.tf           # Provider configuration and requirements
├── variables.tf           # Variable definitions
├── main.tf               # Main resource definitions (droplets, VPC, firewall)
├── outputs.tf            # Output definitions
├── terraform.tfvars.example  # Example configuration file
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Configuration Guide

### Variables

#### Required Variables
- **do_token**: Your DigitalOcean API token (sensitive)

#### Optional Variables with Defaults
- **region** (default: `nyc3`): DigitalOcean region
- **project_name** (default: `my-project`): Project identifier
- **environment** (default: `dev`): Environment type
- **droplets** (default: one web server): Map of droplet configurations
- **ssh_keys** (default: `[]`): SSH keys to add to droplets
- **common_tags** (default: `["terraform", "managed"]`): Tags for all resources
- **enable_monitoring** (default: `false`): Enable DigitalOcean monitoring
- **enable_backups** (default: `false`): Enable automatic backups

### Droplet Configuration

Each droplet in the `droplets` variable accepts:

```hcl
droplet_key = {
  name         = "descriptive-name"      # Required
  image        = "ubuntu-24-04-x64"      # Required
  size         = "s-1vcpu-1gb"           # Required
  backups      = false                   # Optional
  ipv6         = true                    # Optional
  monitoring   = false                   # Optional
  vpc_uuid     = null                    # Optional
  tags         = ["tag1", "tag2"]        # Optional
}
```

### Available Droplet Sizes

Common sizes:
- `s-1vcpu-1gb` - 1 vCPU, 1 GB RAM ($5/month)
- `s-1vcpu-2gb` - 1 vCPU, 2 GB RAM ($12/month)
- `s-2vcpu-2gb` - 2 vCPU, 2 GB RAM ($12/month)
- `s-2vcpu-4gb` - 2 vCPU, 4 GB RAM ($24/month)
- `s-4vcpu-8gb` - 4 vCPU, 8 GB RAM ($48/month)

[Full list of available sizes](https://docs.digitalocean.com/products/droplets/details/specs/)

### Available Images

Popular images:
- `ubuntu-24-04-x64` - Ubuntu 24.04 LTS
- `ubuntu-22-04-x64` - Ubuntu 22.04 LTS
- `debian-12-x64` - Debian 12
- `centos-stream-9-x64` - CentOS Stream 9
- `fedora-40-x64` - Fedora 40

[Browse all available images](https://docs.digitalocean.com/products/droplets/resources/images/)

### Available Regions

- **North America**: `nyc1`, `nyc3`, `sfo1`, `sfo2`, `sfo3`, `tor1`
- **Europe**: `lon1`, `ams2`, `ams3`, `fra1`
- **Asia**: `blr1`, `sgp1`

## 🔐 Security Best Practices

1. **Protect Your API Token**
   - Never commit `terraform.tfvars` to version control
   - Use environment variables for tokens in CI/CD
   - Rotate tokens regularly

2. **SSH Key Management**
   - Add your SSH keys to DigitalOcean before running Terraform
   - Reference them by name in the configuration
   - Never commit private keys to version control

3. **Firewall Configuration**
   - Default firewall rules allow SSH (22), HTTP (80), HTTPS (443)
   - Customize inbound/outbound rules as needed
   - Apply the principle of least privilege

4. **State File Management**
   - Store terraform.tfstate securely
   - Consider using remote state backends (S3, Terraform Cloud)
   - Enable state encryption and locking

5. **Tagging Strategy**
   - Use consistent tags for resource identification
   - Tag by environment (dev, staging, prod)
   - Tag by component (web, database, cache)

## 📊 Common Workflows

### Deploy a Single Web Server

Edit `terraform.tfvars`:
```hcl
droplets = {
  web-01 = {
    name   = "web-server"
    image  = "ubuntu-24-04-x64"
    size   = "s-1vcpu-1gb"
    tags   = ["web"]
  }
}
```

Run:
```bash
terraform plan
terraform apply
```

### Scale Up to Multiple Servers

Edit `terraform.tfvars`:
```hcl
droplets = {
  web-01 = { ... }
  web-02 = { ... }
  web-03 = { ... }
}
```

### Update Server Configuration

Modify the droplet configuration and run:
```bash
terraform plan  # Review changes
terraform apply
```

### Destroy All Infrastructure

```bash
terraform destroy
```

### Import Existing Droplets

If you have existing DigitalOcean droplets, import them:
```bash
terraform import digitalocean_droplet.web[key] droplet_id
```

## 🔍 Useful Commands

```bash
# Show current state
terraform show

# Format configuration files
terraform fmt -recursive

# Validate configuration
terraform validate

# List all resources
terraform state list

# Show specific resource state
terraform state show digitalocean_droplet.web["web-01"]

# Get resource details
terraform output droplet_details
```

## 📈 Monitoring and Logging

### View Droplet Outputs
```bash
# Get all droplet information
terraform output droplet_details

# Get SSH commands
terraform output ssh_command

# Connect to a droplet
# From the output: ssh root@<IP_ADDRESS>
```

### Monitor on DigitalOcean Dashboard
1. Visit [DigitalOcean Console](https://cloud.digitalocean.com)
2. Navigate to Droplets section
3. Resources are tagged with your `project_name` and `environment`

## 🐛 Troubleshooting

### "Invalid token" error
- Verify your DigitalOcean API token is correct
- Check token hasn't expired
- Ensure token has read/write permissions

### "SSH key not found" error
- Add the SSH key to your DigitalOcean account first
- Verify the key name in `ssh_keys` matches exactly
- Check key spelling and case sensitivity

### "Insufficient capacity" error
- Try a different region
- Try a different droplet size
- Wait a few minutes and try again

### State lock timeout
- Another Terraform operation is in progress
- Check for stale lock files in `.terraform/`
- If necessary: `terraform force-unlock <LOCK_ID>`

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Terraform Deploy

on:
  push:
    branches: [main]

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Init
        run: terraform init
        
      - name: Terraform Plan
        run: terraform plan
        env:
          TF_VAR_do_token: ${{ secrets.DIGITALOCEAN_TOKEN }}
          
      - name: Terraform Apply
        run: terraform apply -auto-approve
        env:
          TF_VAR_do_token: ${{ secrets.DIGITALOCEAN_TOKEN }}
```

## 📚 Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [DigitalOcean Terraform Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)
- [DigitalOcean API Documentation](https://docs.digitalocean.com/reference/api/)
- [Terraform Best Practices](https://www.terraform.io/language/expressions/references)

## 📝 Notes

- All droplets are created in a VPC for network isolation
- A firewall is automatically created with common ports open
- Resources follow naming convention: `{project_name}-{description}-{environment}`
- All resources are tagged for easy identification and cost tracking
- The configuration uses `create_before_destroy` lifecycle for zero-downtime updates

## 🤝 Contributing

When modifying this configuration:
1. Always run `terraform validate` and `terraform fmt`
2. Use descriptive variable and resource names
3. Update this README with significant changes
4. Test changes in dev environment first

## 📄 License

This Terraform configuration is provided as-is for infrastructure management.

---

**Last Updated**: October 2025
**Terraform Version**: >= 1.0
**Provider Version**: DigitalOcean ~> 2.0
