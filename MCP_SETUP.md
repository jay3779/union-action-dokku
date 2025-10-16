# Terraform MCP Development Environment Setup

Complete guide for setting up Terraform MCP (Model Context Protocol) integration with Cursor and VS Code.

## Overview

Terraform MCP enables AI tools like Cursor and Claude to:
- Access real-time Terraform Registry documentation
- Understand DigitalOcean provider resources
- Generate production-ready infrastructure code
- Validate configurations against latest specs
- Understand module relationships and dependencies

## Prerequisites

- **Cursor** (latest version) or **VS Code** with Cursor extension
- **Terraform** >= 1.0 installed locally
- **Node.js** >= 18 (for MCP server)
- **DigitalOcean API Token**
- **SSH Key** configured

## Step 1: Install HashiCorp Terraform Extension

### VS Code / Cursor

1. Open Extensions marketplace
2. Search for "HashiCorp Terraform"
3. Install the official **Terraform** extension by HashiCorp
4. Reload the window

**Current Version**: 2.37.5 or later recommended

## Step 2: Verify Language Server Configuration

The `.vscode/settings.json` file includes the correct configuration:

```json
"terraform.languageServer": {
  "enable": true,
  "args": ["serve"]
}
```

✅ **IMPORTANT**: The language server must use `"serve"` argument, not `"lsp"`

If you see errors like:
```
"You need at least a 'serve' argument in the terraform.languageServer.args setting"
```

Verify your settings include `"args": ["serve"]`.

## Step 3: Configure MCP Server

### Using Cursor Settings

1. Open **Cursor Settings** (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Enable MCP support
4. Add Terraform MCP server configuration

### Configuration File Locations

**Cursor**:
- Windows: `%APPDATA%\Cursor\settings.json`
- Mac: `~/Library/Application Support/Cursor/settings.json`
- Linux: `~/.config/Cursor/settings.json`

**VS Code**:
- Windows: `%APPDATA%\Code\User\settings.json`
- Mac: `~/Library/Application Support/Code/User/settings.json`
- Linux: `~/.config/Code/User/settings.json`

### MCP Server Configuration

The project includes `.mcp-config.json`:

```json
{
  "mcpServers": {
    "terraform": {
      "command": "npx",
      "args": ["-y", "@antml/terraform-mcp"],
      "disabled": false,
      "env": {
        "TERRAFORM_DOC_PATH": "https://registry.terraform.io"
      }
    }
  }
}
```

### Add to Cursor/VS Code Settings

In your editor settings, add:

```json
"mcp": {
  "terraform": {
    "command": "npx",
    "args": ["-y", "@antml/terraform-mcp"]
  }
}
```

## Step 4: Initialize Development Environment

### Terminal Setup

```powershell
# Navigate to project
cd C:\Terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format files
terraform fmt -recursive
```

### Environment Variables

Set your DigitalOcean token:

```powershell
# PowerShell - Temporary (current session only)
$env:TF_VAR_do_token = "your_token_here"

# PowerShell - Persistent (add to profile)
# Edit $PROFILE and add:
# $env:TF_VAR_do_token = "your_token_here"

# Or use terraform.tfvars
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit with your values
```

## Step 5: Verify MCP Integration

### Check Extension Status

1. Open Cursor/VS Code
2. Open `main.tf` from this project
3. Hover over a resource (e.g., `digitalocean_droplet`)
4. You should see documentation from Terraform Registry
5. Intellisense should show resource attributes

### Test Language Server

1. Make a small change to a `.tf` file
2. Save the file
3. Check for validation errors/warnings
4. Language server should process and validate

### Verify Terraform Commands

In integrated terminal:

```powershell
terraform version
terraform plan
```

Both should work without errors.

## Step 6: Configure Cursor Rules

Cursor rules file is located at `.cursor/rules/terraform-mcp.mdc`

This file provides:
- MCP tool usage guidelines
- Code generation patterns
- Project structure context
- Security best practices

The rules are automatically loaded by Cursor when working in this project.

## Step 7: Set Up Project Context for MCP

Create a prompt that tells MCP about your infrastructure:

```
You are generating Terraform code for DigitalOcean infrastructure.

Project Context:
- Location: C:\Terraform
- Provider: DigitalOcean
- Base Module: modules/droplet/
- Main Config: providers.tf, variables.tf, main.tf, outputs.tf

When generating code:
1. Use existing module structure
2. Follow variable naming: {project_name}-{description}-{environment}
3. Apply tags from common_tags variable
4. Include security groups and VPC configuration
5. Always validate with: terraform validate && terraform fmt
```

## Step 8: Verify All Components

Run this checklist:

- [ ] HashiCorp Terraform extension installed and enabled
- [ ] Language server configured with `"args": ["serve"]`
- [ ] MCP server configuration in place
- [ ] Terraform initialized (`terraform init` completed)
- [ ] Terraform validates successfully (`terraform validate`)
- [ ] Intellisense shows resource documentation
- [ ] DigitalOcean API token configured
- [ ] Can run `terraform plan` without errors
- [ ] Cursor rules file exists at `.cursor/rules/terraform-mcp.mdc`

## Troubleshooting

### Language Server Not Starting

**Error**: "Server process exited with code 127"

**Solution**:
```powershell
# Restart language server
# VS Code/Cursor: Cmd/Ctrl + Shift + P → Terraform: Restart Language Server

# Or restart the editor entirely
```

**Also check**:
- `terraform` command is in PATH: `terraform version`
- Terraform is version >= 1.0: `terraform version`

### MCP Not Connecting

**Error**: "Cannot connect to server"

**Solution**:
```powershell
# Verify MCP server is available
npx -y @antml/terraform-mcp --version

# Check Node.js is installed
node --version

# Should be >= 18.0.0
```

### Intellisense Not Showing

**Solution**:
1. Close and reopen the file
2. Ensure `.tf` file is in workspace
3. Language server should show in Output panel
4. Check for errors in Cursor/VS Code Output

### Validation Errors on Save

**Solution**:
1. Run `terraform validate` in terminal
2. Fix any syntax errors
3. If errors remain, check variable definitions
4. Ensure required variables are set

### Can't Connect to DigitalOcean

**Error**: "Invalid or expired token"

**Solution**:
```powershell
# Verify token is set
$env:TF_VAR_do_token

# If not set, configure it
$env:TF_VAR_do_token = "your_new_token"

# Or use terraform.tfvars
# Edit terraform.tfvars with correct token
```

## Using MCP for Code Generation

### Example: Generate Load Balancer Configuration

1. Open Cursor/VS Code in this project
2. Create new file or edit `main.tf`
3. Use MCP-enabled prompt:

```
Using Terraform MCP, create a DigitalOcean load balancer that:
- Names follow {project_name}-lb-{environment} pattern
- Routes traffic to the web droplets
- Has health checks configured
- Supports both HTTP and HTTPS
- Is tagged with common_tags variable

Use the existing module structure as reference.
Reference MCP documentation for digitalocean_loadbalancer resource.
```

MCP will:
1. Query Terraform Registry for latest resource docs
2. Understand your module structure
3. Generate production-ready configuration
4. Include proper variables and outputs

### Example: Generate Database Module

```
Using Terraform MCP, create a new database module at modules/database/ that:
- Uses DigitalOcean managed database
- Supports PostgreSQL
- Has variables for size, version, region
- Outputs connection strings
- Is tagged and organized like modules/droplet/

Reference existing modules/droplet/ structure.
Check MCP documentation for digitalocean_database_cluster resource.
```

## Best Practices with MCP

1. **Always Validate**: After MCP generates code
   ```powershell
   terraform validate
   terraform fmt -recursive
   terraform plan
   ```

2. **Review Before Apply**: Always review `terraform plan` output

3. **Test in Dev First**: Generate and test in `dev` environment

4. **Commit Incrementally**: Small commits for each infrastructure change

5. **Use Version Control**: All `.tf` files should be in git

6. **Document Changes**: Update README/DEPLOYMENT_GUIDE as needed

## MCP Tools Available

Through Terraform MCP, you have access to:

| Tool | Purpose |
|------|---------|
| `get_terraform_documentation` | Fetch latest resource/module docs |
| `get_provider_documentation` | DigitalOcean provider specific docs |
| `validate_terraform` | Syntax validation |
| `search_registry` | Find modules in Terraform Registry |

## Recommended Prompting Strategy

When using MCP for infrastructure generation:

```
Step 1: [Infrastructure component]
- Use MCP to get latest documentation
- Follow project naming conventions
- Reference existing modules as templates

Step 2: [Next component]
- Chain dependencies correctly
- Apply security groups and firewalls
- Include all required variables and outputs

Step 3: Validation
- Run terraform validate
- Check variable definitions
- Review security configurations

Do not proceed to next step until current step is complete.
```

## Performance Optimization

### Language Server Settings

For better performance:

```json
{
  "terraform.languageServer": {
    "enable": true,
    "args": ["serve"],
    "timeout": 30
  },
  "terraform.validation.run": "on-save"
}
```

### MCP Server Cache

MCP caches documentation locally. First run may take longer. Subsequent queries are faster.

## Security Considerations

1. **Never commit secrets**: `.gitignore` protects `.tfvars` files
2. **Use environment variables**: For CI/CD integration
3. **Rotate tokens**: Regularly update DigitalOcean tokens
4. **Review MCP output**: AI-generated code may need security audit
5. **Validate before deploy**: Always `terraform plan` before `apply`

## Next Steps

1. ✅ Complete all setup steps above
2. ✅ Verify all components working
3. ✅ Test MCP by generating simple resource
4. ✅ Expand to complex infrastructure
5. ✅ Integrate with CI/CD pipeline

## Resources

- [Terraform MCP on Anthropic](https://modelcontextprotocol.io/)
- [HashiCorp Terraform Extension Docs](https://github.com/hashicorp/vscode-terraform)
- [Cursor AI Documentation](https://cursor.sh/)
- [Terraform Registry - DigitalOcean Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/)

---

**Version**: 1.0
**Last Updated**: October 2025
**Status**: MCP Integration Complete ✅
