# Feature Specification: Autonomous Deploy

**Status**: Draft  
**Created**: 2025-10-16  
**Author**: Admin

---

## Overview

Enable fully autonomous infrastructure deployment through production-grade CI/CD automation, gated approvals per environment, remote state management with locking, security scanning, consistent module-based infrastructure, and a minimal "Drop Deploy DO" workflow for zero-friction application deployments.

### Problem Statement

Current infrastructure requires manual Terraform commands, lacks automated validation and security scanning, uses local state files creating collision risks, lacks environment promotion guardrails, and has no automated path for deploying applications without deep infrastructure knowledge.

### User Value

- **DevOps Engineers**: Confidence in automated, gated deployments with security validation
- **Developers**: Deploy applications without infrastructure expertise using Drop Deploy DO
- **Security Teams**: Automatic security scanning and policy enforcement on all changes
- **Infrastructure**: Environment promotion prevents mistakes, remote state prevents collisions

---

## Scope

### In Scope

- GitHub Actions CI/CD workflows (PR validation, gated main branch apply)
- Remote state backend configuration (Terraform Cloud or DO Spaces/S3)
- Security scanning (tfsec, checkov) with fail-on-critical
- Firewall hardening and validation
- Load balancer and database modules
- Environment promotion (dev auto-apply, staging/prod with approvals)
- GitHub Environments secrets management
- Drop Deploy DO minimal workflow (app manifest, build, push, deploy)
- Comprehensive documentation and examples

### Out of Scope

- Full observability stack (ELK/Prometheus) - baseline DO monitoring only
- Advanced WAF/DDoS features beyond DigitalOcean offerings
- Complex auto-scaling policies beyond DO primitives
- Large-scale FinOps and cost governance
- Multi-region deployment (single region focus)
- Custom policy-as-code (OPA/Conftest) - Phase 2

---

## User Scenarios

### Scenario 1: PR Validation & Gated Main Apply

**Actor**: Developer opens PR with infrastructure changes  
**Trigger**: PR created/updated on GitHub

**Steps**:
1. Developer pushes infrastructure changes to feature branch
2. CI runs terraform fmt -check, validate
3. CI runs tfsec and checkov security scans
4. CI generates terraform plan and posts as PR comment
5. Approver reviews plan and security scan results
6. Developer merges PR to main
7. CI validates again on main
8. Dev environment auto-applies (no approval needed)
9. Staging requires manual approval (approver reviews output)
10. Prod requires manual approval + required reviewers
11. Feature complete - all environments updated

**Outcome**: Infrastructure changes deployed with validation and approval gates per environment

### Scenario 2: Drop Deploy DO Application Deployment

**Actor**: Developer has application ready, uses Drop Deploy DO  
**Trigger**: App directory contains dropdeploy.yml manifest

**Steps**:
1. Developer creates apps/my-app/ directory with code and dropdeploy.yml
2. dropdeploy.yml specifies: framework, port, health path, target envs
3. Developer commits and opens PR
4. CI detects dropdeploy.yml change
5. CI builds Docker image (or generates Dockerfile if missing)
6. CI pushes image to registry (GHCR by default)
7. CI updates Terraform variables with image reference
8. CI generates terraform plan and posts to PR
9. Approver reviews plan (resource creation for new app)
10. PR merges; CI applies Terraform
11. Application deployed to target environments (dev/staging/prod per config)
12. Load balancer serves application with health checks
13. Feature complete - app live with zero-downtime updates

**Outcome**: Application deployed from code to production in single PR

### Scenario 3: Environment Promotion Workflow

**Actor**: Infrastructure change must move from dev → staging → prod  
**Trigger**: Merge to main

**Steps**:
1. Spec change approved on PR
2. Merge to main triggers CI
3. Dev applies automatically (changes live immediately)
4. Staging marked "requires manual approval"
5. Approver reviews staging changes (may differ due to size)
6. Approver clicks "approve" in GitHub Environments
7. Staging applies with same config as dev
8. Prod marked "requires manual approval + required reviewers"
9. Multiple approvers review prod changes
10. All required reviewers approve
11. Prod applies
12. Feature complete - changes promoted safely

**Outcome**: Staged rollout prevents cascading failures

---

## Functional Requirements

### Requirement 1: GitHub Actions CI/CD Workflows

**Description**: Automated workflows validate, scan, plan, and apply Terraform changes with environment-specific gating.

**Acceptance Criteria**:
- [ ] PR workflow runs terraform fmt -check, validate on every PR
- [ ] PR workflow runs tfsec and checkov; fails on critical findings
- [ ] PR workflow generates terraform plan and posts summary to PR comment
- [ ] Plan artifact uploaded; available for download on PR
- [ ] Main branch workflow runs same checks on merge
- [ ] Dev environment auto-applies on main branch merge (no approval)
- [ ] Staging environment requires manual approval before apply
- [ ] Prod environment requires manual approval + 2+ required reviewers
- [ ] Applies are serialized per environment (no parallel conflicting applies)
- [ ] Apply logs show successful resource changes
- [ ] Outputs from apply published in GitHub summary

### Requirement 2: Remote State Management

**Description**: Terraform state stored remotely with environment isolation and locking to prevent collisions.

**Acceptance Criteria**:
- [ ] Remote state backend configured (Terraform Cloud or DO Spaces/S3)
- [ ] Separate state per environment (dev, staging, prod)
- [ ] State locking enabled and functional
- [ ] State encryption enabled
- [ ] Backend credentials never stored in repo
- [ ] terraform state list works independently per environment
- [ ] No local tfstate files in repository (verified via .gitignore)
- [ ] Backup strategy documented

### Requirement 3: Security & Quality Gates

**Description**: Automated security scanning and validation prevent insecure or malformed configurations from reaching production.

**Acceptance Criteria**:
- [ ] tfsec scan runs on every plan; fails build on high/critical findings
- [ ] checkov scan runs on every plan; fails build on high/critical findings
- [ ] terraform validate passes for all files
- [ ] Findings logged with detailed explanations
- [ ] Policy-as-code framework available for Phase 2 enhancement

### Requirement 4: Firewall Hardening

**Description**: Firewall rules corrected to match DigitalOcean provider schema and follow default-deny posture.

**Acceptance Criteria**:
- [ ] Firewall rules use valid source_type or source_addresses (not invalid "app")
- [ ] Default-deny inbound posture enforced
- [ ] Only required ports open (SSH 22, HTTP 80, HTTPS 443)
- [ ] SSH optionally restricted to office CIDR blocks
- [ ] Terraform validate passes for firewall configuration
- [ ] Outbound rules allow required traffic

### Requirement 5: Modular Infrastructure

**Description**: Root configuration uses modules consistently for droplets, load balancers, and databases enabling reuse and maintenance.

**Acceptance Criteria**:
- [ ] modules/droplet/ module exists with comprehensive inputs
- [ ] modules/load_balancer/ module created with forwarding rules, health checks
- [ ] modules/database/ module created with engine/version/size configuration
- [ ] Root main.tf composes modules (no direct resource definitions)
- [ ] Module outputs promoted to root outputs
- [ ] LB and DB modules tested in dev environment
- [ ] Documentation includes module usage examples

### Requirement 6: Environment Promotion

**Description**: Three environments (dev, staging, prod) with appropriate approval gates and resource sizing per environment.

**Acceptance Criteria**:
- [ ] Dev environment: auto-apply on main branch merge
- [ ] Staging environment: manual approval required
- [ ] Prod environment: manual approval + required reviewers
- [ ] Environment-specific resource sizing (prod > staging > dev)
- [ ] Environment-specific secrets and configurations
- [ ] Tagging includes environment identifier
- [ ] Separate Terraform workspaces or backends per environment

### Requirement 7: Secrets Management

**Description**: GitHub Environments stores all secrets; no credentials committed to repository.

**Acceptance Criteria**:
- [ ] GitHub Environments configured (dev, staging, prod)
- [ ] TF_VAR_do_token stored as secret in appropriate environment
- [ ] Backend credentials (Terraform Cloud token or S3 keys) as secrets
- [ ] Registry credentials (if needed) as secrets
- [ ] Log masking enabled (credentials never visible in logs)
- [ ] OIDC authentication preferred where available

### Requirement 8: Drop Deploy DO Workflow

**Description**: Minimal path for deploying applications without manual infrastructure configuration.

**Acceptance Criteria**:
- [ ] dropdeploy.yml manifest file format documented and supported
- [ ] Framework auto-detection (Node.js, Python, Ruby, Go, Static)
- [ ] Dockerfile generation for apps without Dockerfile
- [ ] Docker image built and pushed to registry (GHCR by default)
- [ ] Terraform variables updated with image reference
- [ ] Zero-downtime deployment strategy (blue-green or rolling)
- [ ] Health checks validate deployment success
- [ ] Automatic rollback on health check failure
- [ ] Sample app/dropdeploy.yml provided and tested

---

## Success Criteria

Success is achieved when:

1. **CI/CD Confidence**: All PRs show green checks for fmt, validate, tfsec, checkov; developers confident merging
2. **Gated Safety**: Dev auto-applies; staging/prod require approvals; zero production incidents from unapproved changes
3. **State Security**: Remote state prevents collisions; zero state conflicts; locking prevents corruption
4. **Security Enforcement**: All critical security findings blocked; zero critical findings reaching prod
5. **Module Consistency**: Root uses modules for all infrastructure; LB and DB modules in production use
6. **Drop Deploy Success**: Sample app deploys from code to prod-like environment in < 10 minutes via single PR
7. **Environment Isolation**: Separate secrets per environment; credentials never exposed
8. **Automation Coverage**: > 90% of deployments require zero manual intervention after merge

---

## Key Entities

### CI/CD Pipeline

**Attributes**:
- `workflow_name` (string): terraform-pr, terraform-apply, drop-deploy
- `trigger_event` (string): pull_request, push to main, app changes
- `environment_target` (enum): dev, staging, prod
- `approval_required` (boolean): Auto vs manual
- `status` (enum): pending, running, success, failure

**Relationships**:
- Triggered by GitHub events
- Reads/writes Terraform state
- Validates via security scanning
- Reports via PR comments

### Environment

**Attributes**:
- `name` (enum): dev, staging, prod
- `auto_apply` (boolean): Automatic application of changes
- `required_approvers` (integer): Number of required approvals
- `resource_sizing` (enum): dev/staging/prod tier
- `secrets_scope` (string): GitHub Environment secrets

**Relationships**:
- Has GitHub Environment configuration
- Has environment-specific secrets
- Has environment-specific state file

### Application (Drop Deploy)

**Attributes**:
- `name` (string): Application identifier
- `framework` (enum): nodejs, python, ruby, go, static
- `port` (integer): Application listening port
- `health_path` (string): Health check endpoint path
- `registry` (string): Container registry location
- `image_uri` (string): Built image reference

**Relationships**:
- Built from source code
- Deployed via Terraform
- Served by load balancer
- Monitored for health

---

## Assumptions

- DigitalOcean account and API token already exist
- GitHub repository created with Actions enabled
- GitHub Environments and required reviewers can be configured
- Remote state backend choice (Terraform Cloud vs DO Spaces) will be decided before implementation
- Container registry available (GHCR, DOCR, or Docker Hub)
- Office CIDR blocks known for SSH access restriction
- Team has capacity to review/approve deployments
- DNS/Certificates managed outside this scope (or DO App Platform TLS)
- Security scanning findings can be addressed (no permanent blockers expected)

---

## Dependencies & Constraints

### Dependencies

- GitHub repository with Actions enabled
- DigitalOcean API token with write permissions
- Remote state backend (Terraform Cloud or S3-compatible storage)
- Container registry and credentials
- GitHub Environments feature available (org-level permissions)
- DNS records (if custom domain required for App Platform)

### Constraints

- CI runs must complete in < 15 minutes (plan + scan)
- Security scans must complete in < 5 minutes
- Artifact retention limited (30 days default)
- Concurrent applies serialized per environment (prevent state collisions)
- Drop Deploy apps limited to containerizable frameworks
- Health check timeouts < 60 seconds
- Max 3 approvers recommended for prod (practical approval time)

---

## Edge Cases & Error Handling

### Edge Case 1: Security Scan Finds Critical Issue

**Condition**: tfsec or checkov reports critical finding on PR

**Expected Behavior**: Build fails, PR shows red X, merge blocked, developer must fix issue and push new commit

### Edge Case 2: State Lock Timeout

**Condition**: Another deployment in progress when new deploy triggered

**Expected Behavior**: New deployment waits for lock; applies after previous completes (serialization)

### Edge Case 3: Drop Deploy App Has No Dockerfile

**Condition**: App lacks Dockerfile, only source code provided

**Expected Behavior**: System generates minimal Dockerfile based on framework detection; developer can override

### Edge Case 4: Health Check Fails Post-Deploy

**Condition**: Application deployed but fails health checks

**Expected Behavior**: Automatic rollback to previous version; developer notified of failure with logs

### Error Scenario 1: Invalid Approval Configuration

**Error**: Prod approver count mismatch with GitHub settings

**Recovery**: CI validation catches this; deploy blocked; settings corrected before retry

### Error Scenario 2: Credentials Leak in Logs

**Error**: Secret appears in terraform output or logs

**Recovery**: Log masking hides secret; GitHub audit trail preserved; credentials rotated

---

## Non-Functional Aspects

### Performance

- CI plan generation: < 5 minutes
- Security scanning: < 5 minutes  
- Total PR workflow: < 15 minutes (plan + scan + upload)
- Apply operation: < 10 minutes (typical)
- Drop Deploy build + push: < 10 minutes

### Reliability

- Remote state with locking prevents collisions
- Atomic deployments (all-or-nothing)
- Automatic rollback on health check failure
- Retry-safe applies with idempotent modules
- Zero-downtime updates (create_before_destroy)

### Security

- No credentials in repo; all secrets in GitHub Environments
- Log masking prevents credential exposure
- tfsec/checkov scanning blocks critical findings
- SSH access can be restricted to office CIDR
- State encryption enabled
- OIDC authentication preferred

### Usability

- Clear PR comments showing plan diffs
- Straightforward approval workflow
- Drop Deploy requires only dropdeploy.yml manifest
- Examples provided for common use cases

---

## Glossary

| Term | Definition |
|------|-----------|
| **Gated Apply** | Deployment requires approval before Terraform apply executes |
| **Environment Promotion** | Moving changes through dev → staging → prod with increasing approval requirements |
| **Drop Deploy DO** | Minimal path for deploying applications without infrastructure expertise |
| **dropdeploy.yml** | Application manifest specifying framework, port, target environments |
| **Zero-Downtime Deploy** | Updating application with no service interruption (blue-green or rolling) |
| **State Locking** | Preventing concurrent Terraform operations to avoid state corruption |
| **Serialized Applies** | Ensuring applies happen sequentially per environment (no parallel conflicts) |

---

## Appendix

### Related Documents

- [Enhancement Spec: Autonomous CI/CD](../../enhancement-spec-autonomous.md)
- [Implementation Variables](../../ENHANCEMENT_VARIABLES.md)
- [Project Constitution](../../.specify/memory/constitution.md)

### References

- GitHub Actions Documentation
- Terraform Cloud or S3 Backend Configuration
- DigitalOcean Terraform Provider Documentation
- tfsec and checkov security scanning tools


