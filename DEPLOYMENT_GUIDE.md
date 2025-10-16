# Terraform DigitalOcean - Deployment Guide

A step-by-step guide for deploying infrastructure using this Terraform configuration.

## Prerequisites Checklist

- [ ] Terraform installed locally (version >= 1.0)
- [ ] DigitalOcean account created
- [ ] DigitalOcean API token generated
- [ ] SSH key generated and added to DigitalOcean account
- [ ] Git cloned/checked out
- [ ] Access to this repository

## Step 1: Install Terraform

### Windows with PowerShell

```powershell
# Using Chocolatey
choco install terraform

# Or using Scoop
scoop install terraform

# Verify installation
terraform --version
```

### Download Manually
Visit https://www.terraform.io/downloads and download the Windows binary.

## Step 2: Generate DigitalOcean API Token

1. Log in to [DigitalOcean Dashboard](https://cloud.digitalocean.com)
2. Navigate to **Settings** → **API**
3. Click **Generate New Token**
4. Name it (e.g., "Terraform-Token")
5. Select **Read** and **Write** scopes
6. Click **Generate Token**
7. **Copy and save it securely** (you won't see it again!)

## Step 3: Add SSH Key to DigitalOcean

### Generate SSH Key (if you don't have one)

```powershell
# Open PowerShell
ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\id_rsa
```

### Add Public Key to DigitalOcean

1. Go to [DigitalOcean Dashboard](https://cloud.digitalocean.com) → **Settings** → **Security**
2. Click **Add SSH Key**
3. Paste your public key content (from `~\.ssh\id_rsa.pub`)
4. Name it meaningfully (e.g., "My-Development-Machine")
5. Click **Add SSH Key**

## Step 4: Set Up Terraform

### Clone Repository

```powershell
cd your-projects-folder
git clone <repository-url>
cd Terraform
```

### Initialize Terraform

```powershell
terraform init
```

This downloads the DigitalOcean provider and sets up the `.terraform` directory.

## Step 5: Configure Variables

### Option A: Using Environment Variables (Recommended)

```powershell
# Set DigitalOcean token as environment variable
$env:TF_VAR_do_token = "your_token_here"

# Verify it's set
$env:TF_VAR_do_token
```

### Option B: Using terraform.tfvars File

```powershell
# Copy the example file
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit the file (use your preferred editor)
notepad terraform.tfvars
```

Edit these key values:
```hcl
do_token      = "your_digitalocean_api_token"
project_name  = "my-project"
environment   = "dev"
region        = "nyc3"
ssh_keys      = ["my-ssh-key"]  # Name from Step 3
```

## Step 6: Review Your Configuration

### Validate Configuration

```powershell
terraform validate
```

This checks for syntax errors in your Terraform files.

### Format Files

```powershell
terraform fmt -recursive
```

This formats all `.tf` files to match Terraform standards.

### Plan Deployment

```powershell
terraform plan -out=tfplan
```

This shows what Terraform will create/modify/destroy **without making changes**.

**Review this output carefully!** Look for:
- Correct number of resources
- Correct droplet names, sizes, and regions
- Correct tags and configurations

## Step 7: Deploy Infrastructure

### Apply Configuration

```powershell
# Using the plan file created earlier
terraform apply tfplan

# Or apply directly with approval prompt
terraform apply
```

**First deployment typically takes 2-5 minutes.**

Watch the output for:
```
...
Apply complete! Resources added: X, changed: Y, destroyed: Z

Outputs:

droplet_ips = {
  "web-01" = "123.45.67.89"
  "web-02" = "123.45.67.90"
  ...
}
```

## Step 8: Connect to Your Droplets

### Get SSH Commands

```powershell
terraform output ssh_command
```

Output:
```
ssh_command = {
  "web-01" = "ssh root@123.45.67.89"
  "web-02" = "ssh root@123.45.67.90"
}
```

### Connect via SSH

```powershell
ssh root@123.45.67.89
```

You're now connected to your droplet!

### View All Droplet Details

```powershell
terraform output droplet_details
```

This shows:
- IP addresses (IPv4 and IPv6)
- Droplet IDs
- Status
- Resource specifications
- Creation timestamps

## Common Operations

### View Current State

```powershell
terraform show
```

### Update Configuration

1. Edit `terraform.tfvars` or other `.tf` files
2. Run `terraform plan` to review changes
3. Run `terraform apply` to apply changes

Example: Scale to 5 web servers
```hcl
droplets = {
  web-01 = { ... }
  web-02 = { ... }
  web-03 = { ... }
  web-04 = { ... }
  web-05 = { ... }
}
```

### Add a New Droplet

1. Add to `droplets` map in `terraform.tfvars`
2. Run `terraform plan`
3. Run `terraform apply`

### Remove a Droplet

1. Remove from `droplets` map in `terraform.tfvars`
2. Run `terraform plan` (review before proceeding)
3. Run `terraform apply` (will destroy the removed droplet)

### Destroy All Infrastructure

```powershell
terraform destroy
```

**WARNING:** This will delete ALL droplets, VPC, and firewall!

### Destroy Specific Resources

```powershell
# Remove specific droplet without destroying others
terraform destroy -target='digitalocean_droplet.web["web-01"]'
```

## Troubleshooting

### Error: "Invalid or expired token"

**Solution:**
```powershell
# Verify token is set correctly
$env:TF_VAR_do_token

# Re-set if needed
$env:TF_VAR_do_token = "new_token_here"
```

### Error: "SSH key not found"

**Solution:**
1. Verify SSH key exists in DigitalOcean dashboard
2. Check the exact name in `ssh_keys` variable matches
3. SSH key names are case-sensitive

### Error: "Insufficient capacity in region"

**Solution:**
1. Try a different region (e.g., "sfo3" instead of "nyc3")
2. Try a different droplet size
3. Wait a few minutes and try again

### Droplets not getting SSH key

**Solution:**
1. Add SSH keys BEFORE running `terraform apply`
2. Or manually add key after droplet creation:
   ```powershell
   ssh-copy-id root@123.45.67.89
   ```

### Can't Connect via SSH

**Solution:**
```powershell
# Verify SSH key has correct permissions
icacls $env:USERPROFILE\.ssh\id_rsa

# Test connection with verbose output
ssh -vvv root@123.45.67.89

# Try with explicit key
ssh -i $env:USERPROFILE\.ssh\id_rsa root@123.45.67.89
```

## Best Practices

1. **Always plan before applying**
   ```powershell
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

2. **Commit to git regularly**
   ```powershell
   git add .
   git commit -m "Add web servers"
   git push
   ```

3. **Use descriptive names**
   - Good: `web-server-prod-01`
   - Bad: `server1`, `vm-temp`

4. **Tag resources properly**
   - By environment: `prod`, `staging`, `dev`
   - By component: `web`, `db`, `cache`
   - By team: `backend`, `devops`

5. **Monitor costs**
   - Check DigitalOcean dashboard regularly
   - Use tags for cost allocation
   - Destroy unused environments

6. **Use remote state for teams**
   - Uncomment backend configuration in `providers.tf`
   - Set up S3 or Terraform Cloud state storage
   - Enable state locking to prevent conflicts

7. **Review and test in dev first**
   - Make changes in `dev` environment
   - Test thoroughly
   - Only then promote to `staging` and `prod`

## Getting Help

### Check Terraform Logs

```powershell
# Enable debug logging
$env:TF_LOG = "DEBUG"

# Run command (will show detailed logs)
terraform plan

# Disable debug logging
$env:TF_LOG = ""
```

### State Management

```powershell
# List all resources in state
terraform state list

# Show specific resource
terraform state show 'digitalocean_droplet.web["web-01"]'

# Backup state file
Copy-Item terraform.tfstate terraform.tfstate.backup
```

### Documentation

- [Terraform Docs](https://www.terraform.io/docs)
- [DigitalOcean Provider Docs](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)
- [DigitalOcean API Docs](https://docs.digitalocean.com/reference/api/)

## Next Steps

After initial deployment:

1. **Connect to droplets** and configure applications
2. **Set up load balancing** using DigitalOcean Load Balancer resource
3. **Configure databases** or managed services
4. **Set up monitoring** with DigitalOcean Monitoring
5. **Implement CI/CD** to automate deployments
6. **Set up alerts** for infrastructure changes
7. **Back up state file** securely

---

**Questions?** Refer to README.md or main Terraform documentation.
