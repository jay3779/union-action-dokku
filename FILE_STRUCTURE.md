# Terraform Project File Structure

Complete documentation of all files in this Terraform DigitalOcean infrastructure project.

## Root Level Files

### Core Terraform Configuration

#### `providers.tf`
**Purpose:** Define Terraform version requirements and provider configuration

**Contains:**
- Terraform version requirement (>= 1.0)
- DigitalOcean provider version specification
- Provider authentication configuration
- Backend configuration template (commented out for local state)

**Key Points:**
- Uncomment and configure the `backend` block to use remote state storage
- The `provider` block uses `var.do_token` for authentication

#### `variables.tf`
**Purpose:** Define all input variables for the infrastructure

**Contains:**
- `do_token` - DigitalOcean API authentication (sensitive)
- `region` - DigitalOcean deployment region with validation
- `project_name` - Used for resource naming conventions
- `environment` - Environment type (dev/staging/prod) with validation
- `droplets` - Map defining all droplet configurations
- `ssh_keys` - SSH keys to add to droplets
- `common_tags` - Tags applied to all resources
- `enable_monitoring` - Global monitoring toggle
- `enable_backups` - Global backups toggle

**Key Points:**
- All variables have descriptions for clarity
- Some variables include validation rules
- `droplets` variable uses complex type for flexible configuration

#### `main.tf`
**Purpose:** Define actual infrastructure resources to create

**Contains:**
- Data source for available SSH keys
- VPC (Virtual Private Cloud) resource
- Droplets created from `droplets` variable using `for_each`
- Firewall with inbound/outbound rules
- Firewall-droplet attachment

**Resources Created:**
- `digitalocean_vpc` - Network isolation for resources
- `digitalocean_droplet` - Virtual machines (multiple via for_each)
- `digitalocean_firewall` - Network access control
- `digitalocean_firewall_droplets` - Firewall attachment

#### `outputs.tf`
**Purpose:** Define outputs displayed after Terraform apply

**Contains:**
- `vpc_id` and `vpc_urn` - VPC identification
- `droplet_ips` - Map of droplet names to IP addresses
- `droplet_details` - Complete information about all droplets
- `firewall_id` and `firewall_urn` - Firewall identification
- `ssh_command` - Ready-to-use SSH connection commands

**Key Points:**
- Outputs are displayed automatically after `terraform apply`
- Can be retrieved later with `terraform output`
- Useful for scripts and CI/CD pipelines

### Configuration Files

#### `terraform.tfvars.example`
**Purpose:** Template showing how to configure the infrastructure

**Contains:**
- Example values for all variables
- Commented explanations
- Sample droplet configurations
- Best practice recommendations

**Usage:**
```bash
Copy-Item terraform.tfvars.example terraform.tfvars
# Then edit terraform.tfvars with your specific values
```

**Important Notes:**
- This file is for reference only
- Create actual `terraform.tfvars` (not committed to git)
- Use environment variables for sensitive data in CI/CD

### Documentation Files

#### `README.md`
**Purpose:** Main project documentation and reference guide

**Contains:**
- Project overview and capabilities
- Quick start guide
- Installation instructions
- Configuration reference
- Security best practices
- Common workflows
- Useful commands
- Troubleshooting guide
- CI/CD integration example
- Additional resources

**Audience:** All users and new team members

#### `DEPLOYMENT_GUIDE.md`
**Purpose:** Step-by-step deployment walkthrough for first-time users

**Contains:**
- Prerequisites checklist
- Terraform installation instructions
- API token generation steps
- SSH key setup
- Configuration steps
- Deployment process
- Connection instructions
- Common operations
- Detailed troubleshooting
- Best practices
- Next steps

**Audience:** Developers deploying for the first time

#### `FILE_STRUCTURE.md`
**Purpose:** This file - document the structure and purpose of each file

**Contains:**
- Directory tree overview
- Description of each file
- File purposes and contents
- Usage guidelines

### Git Management

#### `.gitignore`
**Purpose:** Specify files and directories to exclude from version control

**Excludes:**
- `.terraform/` - Provider plugins and modules
- `*.tfstate*` - State files containing sensitive information
- `*.tfvars` - Variable files with credentials
- `.terraform.lock.hcl` - Lock file (optional)
- Plan files and override files
- IDE and OS-specific files

**Important:**
- Protects sensitive data (API tokens, state files)
- Keeps repository clean
- Prevents accidental credential commits

## Module Directory: `modules/droplet/`

Reusable module for creating individual droplets with consistent configuration.

### `modules/droplet/variables.tf`
**Purpose:** Define input variables for the droplet module

**Variables:**
- `name` - Droplet name (required)
- `region` - DigitalOcean region (required)
- `image` - OS image (required)
- `size` - Machine size (required)
- `ssh_keys` - SSH key IDs (optional)
- `backups` - Enable backups toggle
- `monitoring` - Enable monitoring toggle
- `ipv6` - Enable IPv6 toggle
- `vpc_uuid` - VPC assignment
- `tags` - Resource tags
- `user_data` - Initialization script

**Usage Example:**
```hcl
module "web_server" {
  source = "./modules/droplet"
  
  name     = "web-server-01"
  region   = "nyc3"
  image    = "ubuntu-24-04-x64"
  size     = "s-1vcpu-1gb"
  ssh_keys = [data.digitalocean_ssh_keys.available.keys[0].id]
  tags     = ["web", "production"]
}
```

### `modules/droplet/main.tf`
**Purpose:** Define the droplet resource and lifecycle

**Contains:**
- Single `digitalocean_droplet` resource
- Graceful shutdown configuration
- Create-before-destroy lifecycle

**Features:**
- Accepts all necessary parameters
- Handles SSH key attachment
- Ensures zero-downtime updates

### `modules/droplet/outputs.tf`
**Purpose:** Export droplet information from the module

**Outputs:**
- `id` - Droplet ID
- `ipv4_address` - Public IPv4
- `ipv6_address` - Public IPv6
- `ipv4_address_private` - Private IPv4
- `status` - Current status
- `created_at` - Creation timestamp
- `ssh_command` - Formatted SSH command

**Usage:**
```hcl
output "web_server_ip" {
  value = module.web_server.ipv4_address
}
```

## Directory Tree

```
C:\Terraform\
├── providers.tf                    # Provider & version config
├── variables.tf                    # Input variable definitions
├── main.tf                         # Resource definitions
├── outputs.tf                      # Output definitions
├── terraform.tfvars.example        # Example configuration
├── .gitignore                      # Git exclusions
├── README.md                       # Main documentation
├── DEPLOYMENT_GUIDE.md             # Step-by-step guide
├── FILE_STRUCTURE.md               # This file
│
└── modules/
    └── droplet/                    # Reusable droplet module
        ├── variables.tf            # Module inputs
        ├── main.tf                 # Module resources
        └── outputs.tf              # Module outputs
```

## Generated Files (Not Committed)

These files are created by Terraform and excluded via `.gitignore`:

### State Management
- `terraform.tfstate` - Current state of all resources
- `terraform.tfstate.backup` - Automatic backup of previous state
- `.terraform.lock.hcl` - Provider version lock file

### Working Files
- `terraform.tfvars` - Your actual configuration (DO NOT commit)
- `tfplan` - Saved execution plan
- `*.tfstate.*.backup` - Additional state backups

### Terraform Cache
- `.terraform/` - Directory containing provider plugins and modules

## File Naming Conventions

### Terraform Files
- `*.tf` - Terraform configuration (HCL syntax)
- `.tfvars` - Variable value files
- `.tfstate` - State files (binary/JSON)
- `.tfplan` - Execution plans

### Documentation Files
- `*.md` - Markdown documentation
- `DEPLOYMENT_*` - Step-by-step guides
- `README.md` - Main documentation

## Best Practices

### Organization
✅ Keep provider config in `providers.tf`
✅ Group related variables in `variables.tf`
✅ Define resources in `main.tf`
✅ Export values in `outputs.tf`
✅ Use modules for reusable components

### Security
✅ Never commit `terraform.tfvars`
✅ Never commit state files
✅ Never commit `.terraform/` directory
✅ Use environment variables for tokens
✅ Rotate API tokens regularly

### Maintenance
✅ Add comments to complex resources
✅ Keep variables organized and documented
✅ Update documentation when changing structure
✅ Use consistent naming conventions
✅ Review changes before applying

## Adding New Files

### New Resource
1. Add resource to `main.tf` (or separate file if many)
2. Add variables to `variables.tf`
3. Add outputs to `outputs.tf`
4. Update documentation

### New Module
1. Create `modules/module-name/` directory
2. Create `variables.tf`, `main.tf`, `outputs.tf`
3. Call module from main `main.tf`
4. Document in README.md

### New Documentation
1. Create `*.md` file in root
2. Link from `README.md`
3. Use consistent formatting
4. Include examples

## File Modification Checklist

Before committing changes:

- [ ] Run `terraform validate`
- [ ] Run `terraform fmt -recursive`
- [ ] Run `terraform plan` to check for errors
- [ ] Review `terraform plan` output
- [ ] Update documentation if logic changed
- [ ] Do NOT commit `.gitignore` exceptions
- [ ] Do NOT commit state files
- [ ] Do NOT commit variable files
- [ ] Update `.tfvars.example` if variables changed

---

**Last Updated:** October 2025
**Terraform Version:** >= 1.0
**Purpose:** Terraform DigitalOcean Infrastructure Management
