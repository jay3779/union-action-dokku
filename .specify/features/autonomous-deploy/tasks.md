# Implementation Tasks: Autonomous Deploy

**Feature**: Autonomous Deploy (CI/CD + Remote State + Security Gates + Drop Deploy DO)  
**Plan**: `.specify/features/autonomous-deploy/plan.md`  
**Timeline**: Today (Phase 1 Start) + This Week (Phase 1 Design) + Next Week (Phase 2 Engineering)

---

## Task Phases Overview

### Phase 0: DECISION VALIDATION ✅ COMPLETE
- [x] 5 key architectural decisions documented
- [x] Constitution Check passed
- [x] All unknowns resolved

### Phase 1A: TODAY'S TASKS (2-3 hours)
**Immediate non-engineering implementation**

- [ ] TASK-101: GitHub Configuration - Create Environments
- [ ] TASK-102: GitHub Configuration - Add Secrets
- [ ] TASK-103: Terraform Variables - Add Phase 1 Variables
- [ ] TASK-104: Terraform Variables - Update tfvars.example

### Phase 1B: THIS WEEK (10-12 hours)
**Design & documentation tasks**

- [ ] TASK-201: Backend Documentation - Terraform Cloud Guide
- [ ] TASK-202: Backend Documentation - DO Spaces Guide  
- [ ] TASK-203: Firewall Design - Configuration Documentation
- [ ] TASK-204: Drop Deploy - Manifest Schema Documentation
- [ ] TASK-205: Drop Deploy - Create Dockerfile Templates
- [ ] TASK-206: Module Contracts - Document all modules
- [ ] TASK-207: User Documentation - CI/CD Reference
- [ ] TASK-208: User Documentation - Drop Deploy Guide
- [ ] TASK-209: User Documentation - GitHub Setup Guide

### Phase 2: NEXT WEEK (Engineering)
**GitHub Actions workflows, backend setup, module implementation**

---

## TODAY'S TASKS (Phase 1A)

### TASK-101: GitHub Configuration - Create Environments

**Status**: ⏳ PENDING  
**Priority**: P0 (Blocking)  
**Effort**: 30 minutes  
**Dependencies**: None  
**Type**: Configuration (UI-based, no code)

**Description**:
Create three GitHub Environments in the repository settings with appropriate protection rules.

**Requirements**:
1. Navigate to repository Settings → Environments
2. Create environment: `dev`
   - No protection rules (allow immediate deployments)
3. Create environment: `staging`
   - Require approval from: @team-lead (or first approver)
   - Environment reviewers: @team-lead
4. Create environment: `prod`
   - Require approval from: Multiple reviewers (2+)
   - Dismiss stale deployment reviews
   - Restrict to branches: master/main only
   - Custom deployment branches: Allow specified patterns

**Files Affected**:
- GitHub Settings (no files)

**Acceptance Criteria**:
- [ ] Environment `dev` created with no protection rules
- [ ] Environment `staging` created with 1-approver requirement
- [ ] Environment `prod` created with 2+ approvers requirement
- [ ] All environments visible in Settings → Environments
- [ ] Environment names exactly match: dev, staging, prod

**Notes**:
- GitHub Environments are org-level if using organization, repo-level otherwise
- Approvers should be actual GitHub users or teams
- Reference: https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

**Owner**: Team Lead or DevOps Engineer  
**Done When**: All 3 environments created and configured

---

### TASK-102: GitHub Configuration - Add Secrets

**Status**: ⏳ PENDING  
**Priority**: P0 (Blocking)  
**Effort**: 20 minutes  
**Dependencies**: TASK-101 (GitHub Environments created)  
**Type**: Configuration (UI-based, no code)

**Description**:
Add required secrets to each GitHub Environment for CI/CD workflows.

**Requirements**:

**Environment: dev**
1. Add Secret: `TF_VAR_do_token`
   - Value: Your DigitalOcean API token
   - Visibility: Private (not exposed in logs)
2. Add Secret: `terraform_cloud_token`
   - Value: Terraform Cloud API token (or leave empty for now)
3. Add Secret: `REGISTRY_TOKEN`
   - Value: GHCR personal access token (or GitHub token with package write)
4. Add Secret: `GHCR_USERNAME`
   - Value: github (or your GitHub username)

**Environment: staging**
- Copy all secrets from dev (same values)

**Environment: prod**
- Copy all secrets from dev (same values)

**Files Affected**:
- GitHub Secrets (no files)

**Acceptance Criteria**:
- [ ] `TF_VAR_do_token` exists in all 3 environments
- [ ] `terraform_cloud_token` exists in all 3 environments
- [ ] `REGISTRY_TOKEN` exists in all 3 environments
- [ ] `GHCR_USERNAME` exists in all 3 environments (value: "github")
- [ ] Secrets are marked as masked in logs
- [ ] No secrets visible in repository files

**Notes**:
- Secrets can be empty initially (for terraform_cloud_token) but structure must exist
- DigitalOcean token can be created at: https://cloud.digitalocean.com/account/api/tokens
- GitHub Actions OIDC will replace some secrets in Phase 2, but we need the structure now
- Reference: https://docs.github.com/en/actions/security-guides/encrypted-secrets

**Owner**: Team Lead or DevOps Engineer  
**Done When**: All 4 secrets added to all 3 environments

---

### TASK-103: Terraform Variables - Add Phase 1 Variables [P]

**Status**: ⏳ PENDING  
**Priority**: P0 (Blocking)  
**Effort**: 1-1.5 hours  
**Dependencies**: None (can parallelize with TASK-101 & TASK-102)  
**Type**: Implementation (Configuration, no code logic)

**Description**:
Add Phase 1 configuration variables to `variables.tf` based on architectural decisions from Phase 0 planning.

**Requirements**:

Add the following variables to `variables.tf` (use Cursor MCP or manual entry):

```hcl
variable "remote_state_backend" {
  description = "Remote state backend choice"
  type        = string
  default     = "terraform-cloud"
  validation {
    condition     = contains(["terraform-cloud", "do-spaces", "s3"], var.remote_state_backend)
    error_message = "Must be terraform-cloud, do-spaces, or s3"
  }
}

variable "terraform_cloud_org" {
  description = "Terraform Cloud organization name"
  type        = string
  default     = ""
  # Will be provided in terraform.tfvars
}

variable "enable_auto_apply_dev" {
  description = "Auto-apply changes to dev environment on main branch merge"
  type        = bool
  default     = true
}

variable "office_cidr_blocks" {
  description = "Office CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = []
  # Example: ["203.0.113.0/24", "198.51.100.0/25"]
}

variable "enable_tfsec_scan" {
  description = "Enable tfsec security scanning in CI"
  type        = bool
  default     = true
}

variable "enable_checkov_scan" {
  description = "Enable checkov security scanning in CI"
  type        = bool
  default     = true
}

variable "require_approval_staging" {
  description = "Require manual approval before deploying to staging"
  type        = bool
  default     = true
}

variable "require_approval_prod" {
  description = "Require manual approval before deploying to prod"
  type        = bool
  default     = true
}

variable "require_multiple_approvers_prod" {
  description = "Number of approvers required for prod deployments"
  type        = number
  default     = 2
  validation {
    condition     = var.require_multiple_approvers_prod >= 1 && var.require_multiple_approvers_prod <= 5
    error_message = "Must be between 1 and 5 approvers"
  }
}
```

**Files Affected**:
- `variables.tf` (add variables section)

**Acceptance Criteria**:
- [ ] All 9 variables added to variables.tf
- [ ] All variables have descriptions
- [ ] All variables have types
- [ ] All variables have defaults
- [ ] Validation rules present for constrained variables
- [ ] terraform fmt passes
- [ ] terraform validate passes (with minimal Terraform config)

**Notes**:
- Placement: Add after existing `variable` definitions, before outputs
- Use Cursor MCP `/mcp terraform.getDocumentation variable` if needed
- These variables are configuration-only (no implementation logic)

**Owner**: Terraform Developer  
**Done When**: All variables added and terraform validate passes

---

### TASK-104: Terraform Variables - Update terraform.tfvars.example [P]

**Status**: ⏳ PENDING  
**Priority**: P0  
**Effort**: 30 minutes  
**Dependencies**: TASK-103 (Phase 1 variables added to variables.tf)  
**Type**: Documentation + Example (Configuration)

**Description**:
Update `terraform.tfvars.example` with examples of the new Phase 1 variables for user reference.

**Requirements**:

Add to `terraform.tfvars.example`:

```hcl
# Phase 1: CI/CD & Remote State Configuration

# Remote state backend selection
remote_state_backend = "terraform-cloud"  # or "do-spaces" or "s3"

# Terraform Cloud organization (if using terraform-cloud)
terraform_cloud_org = "your-org-name"

# CI/CD automation settings
enable_auto_apply_dev            = true   # Auto-apply to dev on merge
require_approval_staging         = true   # Manual approval for staging
require_approval_prod            = true   # Manual approval for prod
require_multiple_approvers_prod  = 2      # Number of required approvers for prod

# Security scanning
enable_tfsec_scan  = true
enable_checkov_scan = true

# SSH access control (office CIDR blocks)
# Leave empty to allow public SSH, or add office IP ranges for restricted access
office_cidr_blocks = [
  # "203.0.113.0/24",      # Example: Office CIDR
  # "198.51.100.0/25",     # Example: Secondary office
]
```

**Files Affected**:
- `terraform.tfvars.example` (add Phase 1 section)

**Acceptance Criteria**:
- [ ] All 9 Phase 1 variables have examples in tfvars.example
- [ ] Examples include helpful comments
- [ ] Defaults are realistic/safe
- [ ] Office CIDR blocks show example format
- [ ] File can be copied to terraform.tfvars for actual use
- [ ] Comments explain each variable's purpose

**Notes**:
- Add to existing file, don't replace
- Include "Phase 1:" header to separate from existing config
- Make it safe - defaults should not accidentally deploy to prod
- Add instructions: "Copy to terraform.tfvars and update with your values"

**Owner**: Terraform Developer  
**Done When**: terraform.tfvars.example updated with all Phase 1 examples

---

## Execution Flow: TODAY'S TASKS

```
TASK-101 (GitHub Envs)  ─┐
                         ├─→ TASK-102 (GitHub Secrets) ─→ [BLOCK 1 DONE]
TASK-103 (TF Variables) ─┤
[can run in parallel]    └─→ TASK-104 (tfvars.example) ─→ [BLOCK 2 DONE]

Total Time: 2-3 hours
Parallel: YES (TASK-101/103 can run together)
Blocking: TASK-102 needs TASK-101; TASK-104 needs TASK-103
```

---

## Success Criteria: TODAY'S TASKS

**All tasks complete when**:
- ✅ GitHub Environments (dev, staging, prod) created
- ✅ GitHub Secrets added to all environments
- ✅ Terraform variables added to variables.tf
- ✅ terraform.tfvars.example updated with Phase 1 examples
- ✅ terraform validate passes
- ✅ terraform fmt passes
- ✅ No blockers for Phase 1B tasks (this week)

**Verification**:
```bash
# In repository root:
cd C:\Terraform
terraform fmt -check              # Should pass
terraform validate                # Should pass
grep "remote_state_backend" variables.tf  # Should exist
grep "terraform_cloud_org" terraform.tfvars.example  # Should exist
```

---

## THIS WEEK'S TASKS (Phase 1B)

These are queued but NOT for today. Start after TODAY'S TASKS complete.

- [ ] TASK-201: Backend Documentation - Terraform Cloud Guide
- [ ] TASK-202: Backend Documentation - DO Spaces Alternative
- [ ] TASK-203: Firewall Configuration Design Documentation
- [ ] TASK-204: Drop Deploy Manifest Schema
- [ ] TASK-205: Dockerfile Templates (5 frameworks)
- [ ] TASK-206: Module Contracts Documentation
- [ ] TASK-207-209: User Guides

**Estimated Total**: 10-12 hours (spread across week)

---

## TASK STATUS SUMMARY

| Task ID | Name | Status | Priority | Effort | Due |
|---------|------|--------|----------|--------|-----|
| TASK-101 | GitHub Environments | ⏳ PENDING | P0 | 30m | TODAY |
| TASK-102 | GitHub Secrets | ⏳ PENDING | P0 | 20m | TODAY |
| TASK-103 | TF Variables | ⏳ PENDING | P0 | 1-1.5h | TODAY |
| TASK-104 | tfvars.example | ⏳ PENDING | P0 | 30m | TODAY |
| TASK-20x | This Week's Tasks | ⏳ PENDING | P1 | 10-12h | THIS WEEK |

---

## Notes for Implementer

1. **TODAY IS NON-ENGINEERING**: No code writing required for today's tasks
2. **GitHub UI-Based**: TASK-101 and TASK-102 are GitHub Settings UI operations
3. **Configuration Only**: TASK-103 and TASK-104 are adding configuration variables (no implementation logic)
4. **Parallelize**: TASK-101/103 can run simultaneously; TASK-102/104 depend on their predecessors
5. **No Blockers**: All today's tasks can start immediately with no infrastructure setup needed
6. **Approvals**: Once today's tasks complete, get team sign-off before proceeding to Phase 1B

---

**Created**: 2025-10-16  
**Last Updated**: 2025-10-16  
**Status**: Ready to Execute  
**Next**: Begin TASK-101 and TASK-103 in parallel
