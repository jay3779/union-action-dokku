# Enhancement Spec: Implementable Variables

**Source**: enhancement-spec-autonomous.md
**Target Environment**: terraform-spec-kit (Terraform MCP DO + Drop Deploy DO)
**Status**: Actionable variables identified for implementation

---

## 🎯 Core Implementation Variables

### 1. Environment Configuration Variables

**Status**: ✅ READY - Already supported in current setup

```hcl
# Primary environment selector
environment = "dev"      # Options: dev, staging, prod
region      = "nyc3"     # DigitalOcean region

# Environment-specific sizing
environment_sizes = {
  dev = {
    droplet_size    = "s-1vcpu-1gb"
    database_size   = "db-s-1vcpu-1gb"
    lb_size         = null  # Not needed for dev
  }
  staging = {
    droplet_size    = "s-2vcpu-2gb"
    database_size   = "db-s-2vcpu-2gb"
    lb_size         = "lb-small"
  }
  prod = {
    droplet_size    = "s-4vcpu-8gb"
    database_size   = "db-s-4vcpu-4gb"
    lb_size         = "lb-large"
  }
}
```

**Implementation**: Add to `variables.tf` as optional nested map with environment-specific defaults.

---

### 2. Remote State & Backend Variables

**Status**: ⏳ NEEDS IMPLEMENTATION

```hcl
# Remote state configuration
remote_state_backend = "terraform-cloud"  # Options: terraform-cloud, do-spaces, s3

# Terraform Cloud backend
terraform_cloud_org  = "your-org"
terraform_cloud_token = var.terraform_cloud_token  # Sensitive

# DO Spaces backend (S3-compatible)
state_bucket_name     = "terraform-${var.project_name}-${var.environment}"
state_lock_table      = "terraform-locks"
spaces_endpoint       = "https://nyc3.digitaloceanspaces.com"
spaces_access_id      = var.spaces_access_id      # Sensitive
spaces_secret_key     = var.spaces_secret_key     # Sensitive

# Backend configuration metadata
backend_region        = "nyc3"
enable_state_locking  = true
state_encryption      = true
```

**Implementation**: Create `backend-config.tf` and `backend-variables.tf`.

---

### 3. CI/CD Pipeline Variables

**Status**: ⏳ NEEDS IMPLEMENTATION

```hcl
# GitHub Actions integration
github_repo_url       = "https://github.com/jay3779/terraform-spec-kit"
github_branch_main    = "master"

# CI/CD behavior
enable_auto_apply_dev = true          # Auto-apply to dev on merge
require_approval_staging = true       # Manual approval for staging
require_approval_prod = true          # Manual approval for prod
require_multiple_approvers_prod = true # 2+ approvers for prod

# Security scanning
enable_tfsec_scan     = true
enable_checkov_scan   = true
enable_policy_as_code = false         # Phase 2

# Artifact configuration
artifact_retention_days = 30
enable_plan_artifacts = true
enable_log_masking = true
```

**Implementation**: Create `ci-cd-variables.tf` - used by GitHub Actions workflows.

---

### 4. Security & Firewall Variables

**Status**: ⏳ NEEDS IMPLEMENTATION

```hcl
# Firewall security posture
firewall_default_deny = true
firewall_rules = {
  ssh = {
    port       = 22
    protocol   = "tcp"
    restricted = true                    # Restrict to office CIDR
    sources    = var.office_cidr_blocks  # Example: ["203.0.113.0/24"]
  }
  http = {
    port       = 80
    protocol   = "tcp"
    restricted = false
    sources    = ["0.0.0.0/0", "::/0"]
  }
  https = {
    port       = 443
    protocol   = "tcp"
    restricted = false
    sources    = ["0.0.0.0/0", "::/0"]
  }
}

# SSH access control
office_cidr_blocks = []  # CIDR blocks allowed SSH access
allow_public_ssh   = false

# TLS/SSL
enable_ssl_by_default = true
```

**Implementation**: Update existing `main.tf` firewall configuration and add new `security-variables.tf`.

---

### 5. Module Configuration Variables

**Status**: 🟡 PARTIAL - Droplet module exists, LB/DB need implementation

```hcl
# Droplet module variables (existing)
# Already in variables.tf as `droplets` map

# Load Balancer module variables (NEW)
load_balancers = {
  main = {
    name                  = "main-lb"
    region                = var.region
    forwarding_rules = [{
      entry_protocol      = "http"
      entry_port         = 80
      target_protocol    = "http"
      target_port        = 8080
    }, {
      entry_protocol      = "https"
      entry_port         = 443
      target_protocol    = "http"
      target_port        = 8080
    }]
    health_check = {
      protocol = "http"
      port     = 8080
      path     = "/health"
    }
    sticky_sessions = true
    tags = var.common_tags
  }
}

# Database module variables (NEW)
databases = {
  main = {
    name         = "main-db"
    engine       = "pg"              # Options: pg, mysql
    version      = "15"
    size         = "db-s-1vcpu-1gb"
    region       = var.region
    num_nodes    = 1
    trusted_ips  = []                # IPs allowed to connect
    users = [{
      name     = "appuser"
      password = var.db_password     # Sensitive
    }]
    tags = var.common_tags
  }
}
```

**Implementation**: Create `modules/load_balancer/` and `modules/database/` with appropriate variables.

---

### 6. Secrets Management Variables

**Status**: ⏳ NEEDS IMPLEMENTATION

```hcl
# GitHub Environments & Secrets mapping
github_environments = {
  dev = {
    approvers = []  # Auto-approve
  }
  staging = {
    approvers = ["team-lead"]
  }
  prod = {
    approvers = ["team-lead", "security-lead"]
    required_approval_count = 2
  }
}

# Secrets to store in GitHub Environment
required_secrets = {
  TF_VAR_do_token = "DigitalOcean API token"
  backend_token   = "Terraform Cloud or S3 credentials"
  registry_username = "Container registry username"
  registry_token  = "Container registry token"
}
```

**Implementation**: Document in `DEPLOYMENT_GUIDE.md` and create setup script for GitHub Actions.

---

### 7. Drop Deploy DO Variables

**Status**: ⏳ NEEDS IMPLEMENTATION

```hcl
# Drop Deploy application manifest (dropdeploy.yml in app directories)
app_manifest = {
  name          = "sample-app"
  framework     = "nodejs"           # Options: nodejs, python, static, ruby, go
  port          = 8080
  health_path   = "/health"
  registry      = "ghcr.io"          # Options: ghcr.io, docr.io, docker.io
  registry_namespace = "jay3779"
  dockerfile_path = "Dockerfile"     # Optional; generated if missing
  deploy_envs   = ["dev", "staging"] # Target environments
}

# Drop Deploy CI configuration
enable_drop_deploy = true
drop_deploy_registry = "ghcr.io"
drop_deploy_image_tag_strategy = "git-sha"  # Options: git-sha, semver
drop_deploy_zero_downtime = true            # Use blue-green or rolling
```

**Implementation**: Create `drop-deploy.yml` workflow and `dropdeploy.yml` schema documentation.

---

### 8. Tagging & Naming Convention Variables

**Status**: ✅ READY - Partially supported

```hcl
# Naming convention
naming_convention = {
  prefix      = "${var.project_name}-"
  separator   = "-"
  environment = var.environment
  suffix      = ""  # Optional additional suffix
}

# Standard tagging strategy
standard_tags = {
  environment = var.environment
  managed_by  = "terraform"
  project     = var.project_name
  created_by  = "terraform-spec-kit"
  created_at  = var.creation_timestamp
}

# Mandatory tags per environment
mandatory_tag_keys = ["environment", "project", "managed_by"]
```

**Implementation**: Already partially supported; enhance with comprehensive tagging validation.

---

### 9. Monitoring & Observability Variables

**Status**: 🟡 PARTIAL - Basic support exists

```hcl
# Monitoring configuration
enable_monitoring     = true
monitoring_provider   = "do-monitoring"  # DigitalOcean native monitoring

# Alert configuration
alert_thresholds = {
  cpu_usage_percent    = 80
  memory_usage_percent = 85
  disk_usage_percent   = 90
  http_error_rate      = 0.05  # 5%
}

# Log retention
log_retention_days = 30

# Observability outputs needed
emit_monitoring_outputs = true
```

**Implementation**: Document monitoring integration; prepare for observability enhancements (Phase 2).

---

### 10. Cost & Governance Variables

**Status**: 🟡 PARTIAL - Basic support exists

```hcl
# Cost tracking and budgets
enable_cost_tracking = true
monthly_budget_alert = 1000  # USD

# Resource quotas per environment
resource_quotas = {
  dev = {
    max_droplets   = 5
    max_databases  = 2
    max_lb         = 1
    max_storage_gb = 100
  }
  staging = {
    max_droplets   = 10
    max_databases  = 3
    max_lb         = 2
    max_storage_gb = 500
  }
  prod = {
    max_droplets   = 20
    max_databases  = 5
    max_lb         = 3
    max_storage_gb = 1000
  }
}

# Lifecycle rules
auto_shutdown_dev = false  # Keep dev always available
auto_shutdown_staging = true
shutdown_time_staging = "22:00"  # UTC
```

**Implementation**: Add cost governance variables (Phase 2).

---

## 📊 Implementation Priority Matrix

| Variable Group | Priority | Effort | Impact | Status |
|---|---|---|---|---|
| **Environment Config** | P0 | Low | High | ✅ Ready |
| **Remote State** | P0 | Medium | Critical | ⏳ High Priority |
| **CI/CD Pipeline** | P0 | Medium | Critical | ⏳ High Priority |
| **Security/Firewall** | P0 | Low | High | ⏳ High Priority |
| **Modules (LB/DB)** | P1 | Medium | Medium | 🟡 Medium Priority |
| **Drop Deploy** | P1 | High | High | 🟡 Medium Priority |
| **Secrets Management** | P1 | Low | Medium | ⏳ High Priority |
| **Tagging/Naming** | P2 | Low | Medium | ✅ Ready |
| **Monitoring** | P2 | Medium | Medium | 🟡 Planned |
| **Cost/Governance** | P3 | High | Low | ⏳ Phase 2 |

---

## 🔧 Implementation Roadmap

### Phase 1: Core Automation (Weeks 1-2)
- [ ] Remote state backend configuration
- [ ] CI/CD workflows (terraform-pr.yml, terraform-apply.yml)
- [ ] Security scanning (tfsec, checkov) integration
- [ ] Firewall corrections and validation
- [ ] Secrets management in GitHub Environments

### Phase 2: Modules & Deployment (Weeks 3-4)
- [ ] Load balancer module (modules/load_balancer/)
- [ ] Database module (modules/database/)
- [ ] Root refactor to use modules
- [ ] Drop Deploy DO minimal workflow
- [ ] Documentation updates

### Phase 3: Advanced Features (Weeks 5+)
- [ ] Policy-as-code (OPA/Conftest)
- [ ] Cost governance and budgets
- [ ] Advanced monitoring and alerting
- [ ] Multi-region support (optional)
- [ ] Team training and runbooks

---

## 📝 Variable Creation Checklist

Use this to track implementation:

- [ ] Create `backend-config.tf` with remote state variables
- [ ] Create `backend-variables.tf` with backend secrets
- [ ] Create `ci-cd-variables.tf` with GitHub Actions variables
- [ ] Update `security-variables.tf` with firewall rules
- [ ] Create `modules/load_balancer/variables.tf`
- [ ] Create `modules/database/variables.tf`
- [ ] Update `variables.tf` with module configurations
- [ ] Document secrets in GitHub Environments
- [ ] Create dropdeploy.yml schema documentation
- [ ] Update `terraform.tfvars.example` with all new variables

---

## 🚀 Quick Start: Core Phase 1 Variables

For immediate implementation, focus on these:

```hcl
# Add to variables.tf
variable "remote_state_backend" {
  description = "Remote state backend choice"
  type        = string
  default     = "terraform-cloud"
  validation {
    condition     = contains(["terraform-cloud", "do-spaces", "s3"], var.remote_state_backend)
    error_message = "Must be terraform-cloud, do-spaces, or s3"
  }
}

variable "enable_auto_apply_dev" {
  description = "Auto-apply changes to dev environment"
  type        = bool
  default     = true
}

variable "office_cidr_blocks" {
  description = "CIDR blocks allowed SSH access"
  type        = list(string)
  default     = []
}

variable "enable_tfsec_scan" {
  description = "Enable tfsec security scanning"
  type        = bool
  default     = true
}

variable "enable_checkov_scan" {
  description = "Enable checkov security scanning"
  type        = bool
  default     = true
}
```

---

**Document Updated**: 2025-10-16
**Enhancement Spec Reference**: enhancement-spec-autonomous.md
**Next Step**: Begin Phase 1 implementation with remote state backend selection
