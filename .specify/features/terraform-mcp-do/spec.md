# Feature Specification: Terraform Mcp Do

**Status**: Complete
**Created**: 2025-10-16
**Author**: Admin

---

## Overview

A production-ready Terraform development environment for DigitalOcean infrastructure, fully integrated with Terraform MCP (Model Context Protocol) to enable AI-assisted infrastructure generation using Cursor.

### Problem Statement

Organizations need to deploy and manage infrastructure on DigitalOcean programmatically while leveraging AI tools for accelerated development. Traditional manual configuration management is time-consuming and error-prone. Infrastructure-as-code provides version control and reproducibility, but requires extensive manual coding and documentation.

### User Value

Developers and DevOps engineers can now:
- Describe infrastructure needs in plain language
- Have Terraform code automatically generated via MCP
- Deploy production-ready DigitalOcean infrastructure in minutes
- Version control infrastructure with Git
- Collaborate on infrastructure changes
- Scale from single droplets to hundreds of resources
- Maintain consistent security and naming conventions

---

## Scope

### In Scope

- Complete Terraform configuration for DigitalOcean provider
- VPC networking with resource isolation
- Droplet deployment with for_each scaling
- Firewall configuration with SSH/HTTP/HTTPS rules
- SSH key management
- Tag-based resource organization
- Multi-environment support (dev/staging/prod)
- Reusable droplet module
- Terraform MCP server integration with Cursor
- HashiCorp Terraform extension configuration for VS Code
- Language server setup with proper configuration
- Comprehensive documentation (7 markdown files)
- Git security (.gitignore) protecting sensitive files
- Example configuration templates

### Out of Scope

- Load balancer resources (can be added later via MCP)
- Managed databases (can be added later via MCP)
- DNS/domain management beyond droplet setup
- Container orchestration
- Kubernetes configuration
- Monitoring and alerting setup (beyond monitoring flag)
- CI/CD pipeline implementation
- Remote state backend configuration (template provided but not implemented)

---

## User Scenarios

### Primary User Flow: First-Time Developer Setup

**Actor**: DevOps engineer or developer new to this infrastructure

**Trigger**: Need to set up Terraform-based infrastructure management for DigitalOcean

**Steps**:
1. User clones the Terraform repository
2. User reads START_HERE.md for navigation guidance
3. User follows MCP_SETUP.md steps 1-5 to configure environment
4. User initializes Terraform with `terraform init`
5. User sets DigitalOcean API token via environment variable
6. User runs `terraform validate` to verify configuration
7. User opens project in Cursor with MCP enabled
8. Feature complete - environment ready for infrastructure generation

**Outcome**: User has a fully configured development environment ready to generate infrastructure

### Secondary User Flow: Infrastructure Generation with MCP

**Actor**: Developer using Cursor with MCP enabled

**Trigger**: Need to deploy specific infrastructure (e.g., web servers, load balancers)

**Steps**:
1. Developer opens Cursor in project root
2. Developer enables MCP in Cursor settings
3. Developer describes infrastructure need: "Create 3 load-balanced web servers"
4. MCP queries Terraform Registry for latest documentation
5. MCP generates production-ready Terraform configuration
6. Developer reviews generated code
7. Developer runs `terraform plan` to preview changes
8. Developer reviews and approves plan
9. Developer runs `terraform apply` to deploy
10. Feature complete - infrastructure deployed

**Outcome**: Infrastructure deployed via AI-assisted code generation in minutes

### Acceptance Scenarios

**Scenario 1: Basic Single Droplet Deployment**

**Given**: Environment is initialized and MCP is configured
**When**: Developer uses `terraform.tfvars` to configure single droplet
**Then**: `terraform apply` successfully creates droplet with SSH access

**Scenario 2: Multi-Droplet with Firewall**

**Given**: Configuration file defines 3+ droplets
**When**: Developer runs `terraform apply`
**Then**: All droplets created, firewall attached, SSH/HTTP/HTTPS open

**Scenario 3: MCP Code Generation**

**Given**: Cursor with MCP enabled in project directory
**When**: Developer prompts MCP to "add load balancer to web servers"
**Then**: MCP generates load balancer code following project conventions

**Scenario 4: Multi-Environment Setup**

**Given**: Developer needs staging and production environments
**When**: Developer creates separate `.tfvars` files for each environment
**Then**: Can deploy identical infrastructure to different environments independently

---

## Functional Requirements

### Requirement 1: Terraform Core Configuration

**Description**: System must provide complete Terraform configuration for DigitalOcean provider with all necessary resource definitions.

**Acceptance Criteria**:
- [ ] `providers.tf` defines DigitalOcean provider >= 2.0
- [ ] Terraform version requirement >= 1.0 specified
- [ ] `variables.tf` includes all configurable options with validation
- [ ] `main.tf` defines VPC, Droplets, and Firewall resources
- [ ] `outputs.tf` exports SSH commands, IP addresses, and resource details
- [ ] `terraform validate` passes without errors
- [ ] `terraform fmt` formats all files consistently

### Requirement 2: MCP Integration

**Description**: Environment must integrate Terraform MCP for AI-assisted code generation.

**Acceptance Criteria**:
- [ ] `.mcp-config.json` properly configured for Terraform MCP server
- [ ] `.cursor/rules/terraform-mcp.mdc` provides AI context and guidelines
- [ ] MCP can query latest Terraform Registry documentation
- [ ] MCP understands existing module structure
- [ ] Language server provides intellisense for DigitalOcean resources

### Requirement 3: Editor Configuration

**Description**: VS Code and Cursor must be properly configured for Terraform development.

**Acceptance Criteria**:
- [ ] `.vscode/settings.json` configures language server with "serve" args
- [ ] Auto-formatting enabled on save
- [ ] Real-time validation on save
- [ ] `.vscode/extensions.json` recommends HashiCorp Terraform extension
- [ ] Intellisense shows resource attributes

### Requirement 4: Reusable Module Structure

**Description**: System must provide reusable module for scalable droplet deployment.

**Acceptance Criteria**:
- [ ] `modules/droplet/` directory contains variables, main, outputs
- [ ] Module accepts all necessary parameters
- [ ] Module outputs IP addresses and connection information
- [ ] Module can be used with for_each for scaling
- [ ] Module lifecycle configured for zero-downtime updates

### Requirement 5: Security and Git Management

**Description**: System must protect sensitive data and follow security best practices.

**Acceptance Criteria**:
- [ ] `.gitignore` excludes `*.tfstate` files
- [ ] `.gitignore` excludes `*.tfvars` files
- [ ] `.gitignore` excludes `.terraform/` directory
- [ ] `do_token` variable marked sensitive
- [ ] VPC isolates resources from public internet
- [ ] Firewall restricts inbound traffic appropriately
- [ ] SSH key management documented

### Requirement 6: Comprehensive Documentation

**Description**: Project must include thorough documentation for all use cases.

**Acceptance Criteria**:
- [ ] `START_HERE.md` provides quick navigation
- [ ] `MCP_SETUP.md` includes 8-step setup guide
- [ ] `DEPLOYMENT_GUIDE.md` covers first-time deployment
- [ ] `README.md` serves as complete reference
- [ ] `FILE_STRUCTURE.md` documents project organization
- [ ] `ENVIRONMENT_READY.md` provides setup verification checklist
- [ ] All documentation includes troubleshooting sections
- [ ] Code examples use PowerShell for Windows compatibility

### Requirement 7: Configuration Examples

**Description**: Project must provide clear configuration examples for users.

**Acceptance Criteria**:
- [ ] `terraform.tfvars.example` shows all variables with examples
- [ ] Example includes single-droplet, multi-droplet, and multi-environment setups
- [ ] Comments explain each configuration option
- [ ] Examples are copy-paste ready for users

---

## Success Criteria

Success is achieved when:

1. **Setup Time**: First-time users can complete MCP setup in under 30 minutes following MCP_SETUP.md
2. **Validation**: `terraform validate` passes with 0 errors, `terraform plan` succeeds with valid DigitalOcean token
3. **MCP Integration**: Cursor with MCP can generate DigitalOcean Terraform code that validates without syntax errors
4. **Documentation Completeness**: 7 markdown files provide clear guidance for setup, deployment, and troubleshooting
5. **Security**: No DigitalOcean tokens or state files accidentally committed to git
6. **Scalability**: Module structure enables deployment from 1 to 100+ droplets without code duplication
7. **DX (Developer Experience)**: Language server provides intellisense, auto-formatting works on save, real-time validation active
8. **Team Collaboration**: New team members can onboard using documentation and deploy infrastructure independently

---

## Key Entities

### Droplet

**Attributes**:
- `name` (string): Descriptive name following `{project_name}-{description}-{environment}` pattern
- `image` (string): OS image slug (e.g., "ubuntu-24-04-x64")
- `size` (string): Machine size slug (e.g., "s-1vcpu-1gb")
- `region` (string): DigitalOcean region (e.g., "nyc3")
- `backups` (boolean): Enable automatic backups
- `monitoring` (boolean): Enable performance monitoring
- `ipv6` (boolean): Enable IPv6 connectivity
- `tags` (list): Resource tags for organization

**Relationships**:
- Belongs to VPC for network isolation
- Protected by Firewall for access control
- Connected via SSH using configured keys

### VPC (Virtual Private Cloud)

**Attributes**:
- `name` (string): Descriptive name
- `description` (string): Purpose of the VPC
- `region` (string): Deployment region

**Relationships**:
- Contains multiple Droplets for network isolation
- Used by Firewall for traffic control

### Firewall

**Attributes**:
- `name` (string): Descriptive name
- `inbound_rules` (list): Traffic rules for ingress
- `outbound_rules` (list): Traffic rules for egress
- `tags` (list): Resource organization

**Relationships**:
- Protects one or more Droplets
- Defines SSH (port 22), HTTP (port 80), HTTPS (port 443) access

---

## Assumptions

- Users have DigitalOcean account and API token already created
- Users have generated SSH keys and added public key to DigitalOcean
- Terraform >= 1.0 installed on developer machines
- Windows-based development (PowerShell as primary shell)
- Users understand basic Git workflows
- DigitalOcean provider documentation available via Terraform Registry MCP
- Cursor is the primary AI development environment
- For initial implementation, single region deployments (no multi-region complexity)
- Standard web server use case is primary (HTTP/HTTPS/SSH access)
- State files stored locally for single-developer workflows (remote backend commented out for team use)

---

## Dependencies & Constraints

### Dependencies

- DigitalOcean API (external service)
- Terraform >= 1.0 (developer tool)
- DigitalOcean Provider >= 2.0 (Terraform plugin)
- Cursor or VS Code (editor)
- HashiCorp Terraform extension
- Node.js >= 18 (for MCP server)
- Git (version control)

### Constraints

- DigitalOcean account required with API token
- SSH key must exist before droplet creation
- Firewall rules constrained to TCP/UDP protocols (no custom protocols)
- Resource naming must follow `{project_name}-{description}-{environment}` pattern
- Only 3 environments supported: dev, staging, prod
- Billing: User responsible for DigitalOcean costs
- Regional availability: Limited to DigitalOcean regions listed in documentation

---

## Edge Cases & Error Handling

### Edge Case 1: Invalid API Token

**Condition**: User provides expired or invalid DigitalOcean token

**Expected Behavior**: `terraform plan` fails with clear "Invalid token" error; user prompted to regenerate token

### Edge Case 2: SSH Key Not Found

**Condition**: Configuration references SSH key that doesn't exist in DigitalOcean account

**Expected Behavior**: `terraform apply` fails with "SSH key not found" error; documentation directs user to add key first

### Edge Case 3: Region Capacity Exceeded

**Condition**: Requested droplet size unavailable in specified region

**Expected Behavior**: `terraform apply` fails with "Insufficient capacity" error; user tries different region or size

### Edge Case 4: Port Already in Use

**Condition**: Firewall rule conflicts with existing firewall

**Expected Behavior**: Firewall attachment fails with clear error; terraform state remains clean for retry

### Error Scenario 1: Missing terraform.tfvars

**Error**: User hasn't created terraform.tfvars file

**Recovery**: Documentation provides example file; user copies terraform.tfvars.example and customizes

### Error Scenario 2: Language Server Connection Error

**Error**: VS Code/Cursor cannot start language server

**Recovery**: MCP_SETUP.md troubleshooting section provides restart steps and diagnostics

---

## Non-Functional Aspects

### Performance

- `terraform plan` completes within 5 seconds with DigitalOcean API latency
- Language server intellisense responsive (< 1 second latency)
- `terraform apply` for 3 droplets completes within 2-3 minutes

### Usability

- Documentation written for non-technical stakeholders where possible
- All examples use Windows PowerShell commands
- Code formatted with consistent 2-space indentation
- Clear error messages guide users to solutions

### Security

- Sensitive data (tokens) never committed to git
- State files containing sensitive info protected by .gitignore
- VPC provides network isolation from public internet
- Firewall restricts SSH to authorized sources
- SSH keys managed by DigitalOcean (not stored in code)
- Module follows least-privilege principle

### Accessibility

- Markdown files readable in all text editors
- No external tools required (except Terraform, Cursor, Git)
- Documentation includes keyboard shortcuts for common tasks
- Troubleshooting section covers common issues

---

## Glossary

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - allows AI tools to query real-time documentation and understand code context |
| **IaC** | Infrastructure as Code - managing infrastructure through code and version control |
| **Terraform** | Infrastructure-as-code tool for provisioning cloud resources declaratively |
| **Droplet** | DigitalOcean's term for a virtual machine/compute instance |
| **VPC** | Virtual Private Cloud - isolated network environment for resources |
| **Firewall** | Network security layer controlling inbound/outbound traffic |
| **Provider** | Terraform plugin that communicates with cloud provider API |
| **State File** | File tracking current infrastructure state; kept in sync with deployed resources |
| **Module** | Reusable Terraform configuration package |
| **for_each** | Terraform feature for deploying multiple similar resources |

---

## Appendix

### Files Delivered

- 4 core Terraform configuration files (providers.tf, variables.tf, main.tf, outputs.tf)
- 3 module files (modules/droplet/)
- 7 comprehensive documentation files
- 4 MCP and editor integration files
- 2 template files for Speckit (.specify/)
- 1 PowerShell script for Speckit

**Total: 23 project files**

### Implementation Statistics

| Metric | Value |
|--------|-------|
| Lines of Code (Terraform) | ~400 |
| Lines of Documentation | ~3,500 |
| Setup Time (first-run) | 30 minutes |
| Deploy Time (first-run) | 2-5 minutes |
| Modules Created | 1 (droplet) |
| Environments Supported | 3 (dev/staging/prod) |
| Resource Types | 5 (VPC, Droplet, Firewall, Firewall Rules, SSH Data Source) |
| Production Ready | Yes ✅ |

### Related Documents

- [KubeBlogs Article on Terraform MCP](https://www.kubeblogs.com/supercharge-terraform)
- [Terraform Documentation](https://www.terraform.io/docs)
- [DigitalOcean Provider Docs](https://registry.terraform.io/providers/digitalocean/digitalocean/)
- [Cursor AI Documentation](https://cursor.sh/)

### References

- Terraform Best Practices
- Infrastructure as Code Principles
- Security Best Practices for Cloud Infrastructure
- Model Context Protocol Specification


