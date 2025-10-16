# Implementation Plan: Autonomous Deploy

**Branch**: `spec/autonomous-deploy` | **Date**: 2025-10-16 | **Spec**: [spec.md](./spec.md)  
**Planning Focus**: Phase 0-1 | **Scope**: Decisions, Design, Configuration (No Engineering)

---

## Summary

Enable fully autonomous infrastructure deployment through production-grade CI/CD automation, gated approvals per environment, remote state management with locking, security scanning, modular infrastructure, and a minimal Drop Deploy DO workflow for zero-friction app deployments.

**Current Status**: Specification complete. Planning identifies what can be implemented now without writing code.

---

## Technical Context

**Infrastructure Platform**: DigitalOcean  
**IaC Tool**: Terraform (v1.0+)  
**Language/Version**: HCL (Terraform language), YAML (GitHub Actions)  
**Primary Dependencies**: 
- GitHub Actions (CI/CD orchestration)
- Terraform Cloud or DO Spaces/S3 (Remote state)
- tfsec, checkov (Security scanning)
- DigitalOcean Terraform Provider (~> 2.0)

**Storage**: Terraform state (remote backend TBD), GitHub repository  
**Testing**: Terraform validate, tfsec, checkov  
**Target Platform**: GitHub + DigitalOcean cloud  
**Project Type**: Infrastructure-as-Code (Terraform modules + CI/CD workflows)  
**Performance Goals**: 
- CI plan generation: < 5 minutes
- Security scanning: < 5 minutes
- Total PR workflow: < 15 minutes
- Apply operation: < 10 minutes
- Drop Deploy build + push: < 10 minutes

**Constraints**:
- CI runs must complete < 15 minutes
- Applies serialized per environment (no parallel)
- Drop Deploy apps limited to containerizable frameworks
- Health check timeouts < 60 seconds

**Scale/Scope**: 
- 3 environments (dev, staging, prod)
- Multi-tenant droplet infrastructure
- Up to 20 droplets in prod (per quota)

---

## Constitution Check

**GATE: Must pass before proceeding. Re-check after Phase 1 design.**

### Project Constitution Alignment (v1.0.0)

| Principle | Requirement | Status |
|-----------|-------------|--------|
| **1. Security First** | Gated applies, fail on security findings | ✅ Designed |
| **2. Production-Ready** | Multi-env promotion, zero-downtime | ✅ Designed |
| **3. IaC Governance** | Remote state, module consistency | ✅ Designed |
| **4. Comprehensive Specs** | All features specified before implementation | ✅ Complete |
| **5. Multi-Environment** | Dev/staging/prod with appropriate gates | ✅ Designed |
| **6. Documentation** | All features documented with examples | ✅ Planned |
| **7. AI-Assisted + Human Review** | MCP integration, approval gates | ✅ Designed |
| **8. Testability** | Validate, scan, plan before apply | ✅ Designed |

**Gate Status**: ✅ **PASS** - All constitution principles addressed in design

---

## Phase 0: Research & Decisions

**Objective**: Resolve all technical decisions and document rationale.

### Decision 1: Remote State Backend

**Decision Point**: Terraform Cloud vs DO Spaces/S3?

**Analysis**:

| Aspect | Terraform Cloud | DO Spaces/S3 |
|--------|-----------------|--------------|
| **Cost** | Free tier limited, paid at $20/month | DO Spaces: $5/month (250GB) |
| **Setup** | GitHub OIDC ready, one-click integration | Requires S3-compatible config |
| **State Locking** | Built-in with workspace isolation | Must enable via DynamoDB or S3 versioning |
| **Security** | Managed encryption, audit logs | Encryption optional, in Spaces |
| **Reliability** | Managed service, 99.9% SLA | Depends on DO infrastructure |
| **Team Size** | Better for teams | Better for cost-conscious small teams |
| **Integration** | Native GitHub Actions support | Manual env var setup |

**Recommendation**: **Terraform Cloud for Phase 1**
- Free tier sufficient for testing
- GitHub Actions native integration saves config work
- Can migrate to DO Spaces later if needed
- Simpler operations (no DynamoDB locking setup)

**Action**: Document Terraform Cloud setup steps in DEPLOYMENT_GUIDE.md

### Decision 2: Deployment Target for Drop Deploy DO

**Decision Point**: DigitalOcean App Platform vs Droplet + Load Balancer?

**Analysis**:

| Aspect | App Platform | Droplet + LB |
|--------|--------------|--------------|
| **Zero-Downtime** | Built-in rolling updates | Must manage blue-green |
| **Complexity** | Managed (simpler) | Self-managed (complex) |
| **Cost** | $5/month minimum per app | Variable (droplet + LB cost) |
| **Control** | Limited (managed platform) | Full control |
| **Health Checks** | Automatic | Manual configuration |
| **Scaling** | Automatic | Manual/via Terraform |
| **Cold Start** | ~30 seconds | Immediate |

**Recommendation**: **Phase 2 Strategy - Start with Droplet + LB**
- More control for current complexity
- Lower cost for testing
- Example apps can run simple containers
- App Platform available as Phase 2 upgrade path

**Action**: Design Terraform modules for droplet + LB + health checks

### Decision 3: Container Registry

**Decision Point**: GHCR vs DOCR vs Docker Hub?

**Analysis**:

| Aspect | GHCR | DOCR | Docker Hub |
|--------|------|------|-----------|
| **Auth** | GitHub OIDC built-in | DO token | Docker credentials |
| **Cost** | Free (private images) | Included with DO | Free tier limited |
| **Speed** | Integrated with GitHub | Fast in DO region | Varies |
| **Retention** | 90 days (free) | Configurable | Forever |

**Recommendation**: **GitHub Container Registry (GHCR)**
- GitHub Actions OIDC integration (no secrets needed for CI)
- Free private images
- Already using GitHub for source code
- Reduces external dependencies

**Action**: Configure GHCR credentials in GitHub Environments

### Decision 4: SSH Access Policy

**Decision Point**: Restrict to office CIDR or allow public?

**Analysis**:
- **Public SSH (0.0.0.0/0)**: Easier for testing, less secure
- **Restricted SSH (office CIDR)**: More secure, operational friction
- **Key-based only**: Always enforced (SSH keys required)

**Recommendation**: **Start with office CIDR restriction**
- Users provide office CIDR blocks in terraform.tfvars
- Default to empty list for flexibility
- Can whitelist specific IPs per environment

**Action**: Add office_cidr_blocks variable to variables.tf

### Decision 5: Policy-as-Code

**Decision Point**: Implement now or Phase 2?

**Recommendation**: **Phase 2 (not now)**
- Core CI/CD workflow takes priority
- Can add OPA/Conftest enforcement after stability
- tfsec/checkov provide sufficient Phase 1 coverage

**Action**: Document policy-as-code as Phase 3 enhancement

### ✅ Research Complete

**Decisions Documented**:
- ✅ Remote backend: Terraform Cloud
- ✅ Drop Deploy target: Droplet + LB (Phase 2: App Platform)
- ✅ Registry: GHCR
- ✅ SSH policy: Office CIDR restriction
- ✅ Policy-as-code: Phase 2+

---

## Phase 1: Design & Configuration

**Objective**: Design what can be configured NOW without engineering/coding.

### What CAN Be Done Now (No Code)

#### ✅ 1. GitHub Configuration

**Can implement now?** YES

**Tasks**:
1. **Create GitHub Environments** (in Settings → Environments)
   - [ ] Create environment: `dev` (no protections)
   - [ ] Create environment: `staging` (require approvals from team-lead)
   - [ ] Create environment: `prod` (require 2+ approvers + reviewers)

2. **Configure GitHub Secrets** (per environment)
   - [ ] `dev`: TF_VAR_do_token, terraform_cloud_token, REGISTRY_TOKEN
   - [ ] `staging`: Same as dev
   - [ ] `prod`: Same as staging

3. **Document Secret Setup** (in DEPLOYMENT_GUIDE.md)
   - [ ] Step-by-step: create GitHub Environments
   - [ ] Step-by-step: add secrets to each environment
   - [ ] Security best practice: rotate tokens quarterly

#### ✅ 2. Terraform Variables Configuration

**Can implement now?** YES

**Changes needed in variables.tf**:
```hcl
# Add these variables (no code changes needed, just config decisions)
- remote_state_backend (string: "terraform-cloud")
- terraform_cloud_org (string: user-provided)
- enable_auto_apply_dev (bool: true)
- office_cidr_blocks (list: user-provided)
- enable_tfsec_scan (bool: true)
- enable_checkov_scan (bool: true)
```

**Tasks**:
1. [ ] Review ENHANCEMENT_VARIABLES.md section on Phase 1 variables
2. [ ] Add variables to variables.tf (can use Cursor MCP for generation)
3. [ ] Update terraform.tfvars.example with Phase 1 variables
4. [ ] Validate terraform format

#### ✅ 3. Backend Configuration

**Can implement now?** YES (partially)

**Design tasks**:
1. [ ] Create backend-config.tf template (ready for manual Terraform Cloud config)
2. [ ] Document: "How to configure Terraform Cloud backend" in DEPLOYMENT_GUIDE.md
3. [ ] Document: "How to configure DO Spaces backend" as Phase 1 alternative
4. [ ] Document: State migration steps (local → remote)

#### ✅ 4. CI/CD Workflow Structure

**Can implement now?** YES (design + templates)

**Design tasks**:
1. [ ] Map GitHub Actions workflows needed:
   - [ ] `.github/workflows/terraform-pr.yml` (format, validate, scan, plan)
   - [ ] `.github/workflows/terraform-apply.yml` (apply with gating)
   - [ ] `.github/workflows/drop-deploy.yml` (app build + deploy)

2. [ ] Create workflow templates (YAML structure, not full implementation):
   - [ ] PR workflow: jobs for fmt, validate, tfsec, checkov, plan
   - [ ] Apply workflow: jobs for dev (auto), staging (manual), prod (manual)
   - [ ] Drop Deploy: jobs for build, push, update vars, plan, apply

3. [ ] Document: "GitHub Actions workflow reference" in .specify/

#### ✅ 5. Firewall & Security Configuration

**Can implement now?** YES

**Design tasks**:
1. [ ] Create firewall-config.md documenting:
   - [ ] SSH: port 22, restricted to office_cidr_blocks (variable)
   - [ ] HTTP: port 80, open to 0.0.0.0/0 and ::/0
   - [ ] HTTPS: port 443, open to 0.0.0.0/0 and ::/0
   - [ ] Default-deny inbound posture

2. [ ] Validate firewall rules against DO provider schema
   - [ ] Ensure all source_type values are valid
   - [ ] Ensure no "app" source_type (invalid in DO)

#### ✅ 6. Module Structure & Contracts

**Can implement now?** YES (design)

**Design tasks**:
1. [ ] Design data-model.md documenting:
   - [ ] **CI/CD Pipeline entity**: workflow_name, trigger_event, environment_target, approval_required, status
   - [ ] **Environment entity**: name, auto_apply, required_approvers, resource_sizing, secrets_scope
   - [ ] **Application entity**: name, framework, port, health_path, registry, image_uri

2. [ ] Create module design document (modules/):
   - [ ] modules/droplet/: inputs (name, image, size, ssh_keys, vpc_uuid, tags, user_data)
   - [ ] modules/load_balancer/: inputs (name, forwarding_rules, health_check, target_tags, sticky_sessions)
   - [ ] modules/database/: inputs (engine, version, size, trusted_sources, users, passwords)

3. [ ] Create API contracts (GitHub Actions inputs/outputs):
   - [ ] terraform-pr.yml outputs: plan_summary, scan_results, artifacts
   - [ ] terraform-apply.yml inputs: environment, dry_run

#### ✅ 7. Drop Deploy DO Configuration

**Can implement now?** YES

**Design tasks**:
1. [ ] Create dropdeploy.yml schema documentation
   - [ ] Fields: name, framework, port, health_path, registry, registry_namespace, deploy_envs
   - [ ] Valid frameworks: nodejs, python, ruby, go, static
   - [ ] Valid registries: ghcr.io, docr.io, docker.io

2. [ ] Create Dockerfile template directory: apps/templates/
   - [ ] [ ] nodejs/Dockerfile (Node.js template)
   - [ ] [ ] python/Dockerfile (Python template)
   - [ ] [ ] ruby/Dockerfile (Ruby template)
   - [ ] [ ] go/Dockerfile (Go template)
   - [ ] [ ] static/Dockerfile (Static site template)

3. [ ] Create sample app: apps/sample-nodejs/
   - [ ] [ ] app.js (simple Express server)
   - [ ] [ ] package.json
   - [ ] [ ] dropdeploy.yml (manifest)
   - [ ] [ ] .gitignore

4. [ ] Document: "Drop Deploy DO getting started" in .specify/

#### ✅ 8. Documentation & Quickstart

**Can implement now?** YES

**Design tasks**:
1. [ ] Update README.md with:
   - [ ] CI/CD architecture overview
   - [ ] Environment promotion flow (dev → staging → prod)
   - [ ] Link to CI/CD workflows reference

2. [ ] Update DEPLOYMENT_GUIDE.md with:
   - [ ] "Phase 1: Setup Remote State" section
   - [ ] "Phase 1: Configure GitHub Environments & Secrets" section
   - [ ] "Phase 1: Enable CI/CD Workflows" section
   - [ ] "Phase 1: Drop Deploy DO setup" section

3. [ ] Create CI/CD_REFERENCE.md:
   - [ ] Workflow architecture diagrams (ASCII)
   - [ ] PR validation flow
   - [ ] Apply flow with gating
   - [ ] Drop Deploy flow

4. [ ] Create QUICKSTART.md for autonomous-deploy:
   - [ ] 5-minute overview of CI/CD automation
   - [ ] 10-minute setup checklist
   - [ ] First PR walkthrough

---

## What CANNOT Be Done Yet (Requires Engineering)

❌ **GitHub Actions Workflow Implementation**
- Requires writing YAML workflow files (Phase 2 engineering)
- Requires testing with actual GitHub Actions runner
- Depends on scripts/runners availability

❌ **Terraform Backend Configuration**
- Requires Terraform commands to be executed
- Requires credentials to be stored and tested
- Depends on Terraform Cloud/DO Spaces setup

❌ **Module Implementation**
- Requires HCL module coding
- Requires local terraform apply testing
- Requires DigitalOcean resource testing

❌ **Sample App Creation**
- Requires application code implementation
- Requires Docker image building and testing
- Requires container registry credential setup

---

## Project Structure (Design)

### Documentation (Current Feature)

```
.specify/features/autonomous-deploy/
├── spec.md                              # Feature specification ✅ DONE
├── plan.md                              # This file (Phase 1 planning) 🔄 IN PROGRESS
├── research.md                          # Phase 0 research (decisions documented above)
├── data-model.md                        # Phase 1 data model design
├── quickstart.md                        # Phase 1 quickstart
├── contracts/
│   ├── github-actions-inputs.md         # GitHub Actions API contract
│   ├── terraform-variables.md           # Terraform variable contract
│   └── drop-deploy-manifest.md          # dropdeploy.yml contract
└── checklists/
    └── requirements.md                  # Quality checklist ✅ DONE
```

### Configuration & Templates (Root)

```
.github/workflows/                       # To be created in Phase 2 engineering
├── terraform-pr.yml                     # PR validation workflow (template ready)
├── terraform-apply.yml                  # Apply with gating workflow (template ready)
└── drop-deploy.yml                      # Drop Deploy workflow (template ready)

backend-config/                          # New - Backend configuration templates
├── terraform-cloud.md                   # Terraform Cloud setup guide
└── do-spaces.md                         # DO Spaces setup guide

Terraform/                               # Existing
├── variables.tf                         # To add Phase 1 variables
├── terraform.tfvars.example             # To add Phase 1 examples
├── firewall-config.md                   # New - Firewall design
└── modules/
    ├── droplet/                         # Existing
    ├── load_balancer/                   # New (design ready)
    └── database/                        # New (design ready)

apps/                                    # New - Drop Deploy applications
├── templates/
│   ├── nodejs/Dockerfile                # Dockerfile template
│   ├── python/Dockerfile
│   ├── ruby/Dockerfile
│   ├── go/Dockerfile
│   └── static/Dockerfile
└── sample-nodejs/
    ├── app.js                           # Sample app
    ├── package.json
    ├── dropdeploy.yml                   # Manifest
    └── Dockerfile                       # Generated example
```

---

## Implementable Tasks (No Engineering)

### Priority: IMMEDIATE (Can do today)

1. **Decision Documentation** ✅ DONE
   - [x] Document 5 key decisions with rationale
   - [x] Add to research.md

2. **GitHub Configuration Plan**
   - [ ] Create setup checklist for GitHub Environments
   - [ ] Create setup checklist for GitHub Secrets
   - [ ] Add to DEPLOYMENT_GUIDE.md

3. **Variables Design**
   - [ ] Review Phase 1 variables from ENHANCEMENT_VARIABLES.md
   - [ ] Create variables.tf update checklist
   - [ ] Example: office_cidr_blocks, enable_tfsec_scan, etc.

4. **Documentation Updates**
   - [ ] Update DEPLOYMENT_GUIDE.md Phase 1 section
   - [ ] Create CI/CD_REFERENCE.md skeleton
   - [ ] Create backend-config/ templates

### Priority: NEAR-TERM (This week)

5. **Data Model Design**
   - [ ] Create data-model.md with entities
   - [ ] Document CI/CD Pipeline, Environment, Application entities
   - [ ] Add validation rules

6. **API Contracts**
   - [ ] Create contracts/ directory
   - [ ] Document GitHub Actions workflow inputs/outputs
   - [ ] Document Terraform variable contract
   - [ ] Document dropdeploy.yml manifest schema

7. **Drop Deploy Design**
   - [ ] Create dropdeploy.yml schema documentation
   - [ ] Create Dockerfile templates (5 frameworks)
   - [ ] Create sample app structure
   - [ ] Document Drop Deploy workflow

8. **Module Contracts**
   - [ ] Document modules/load_balancer/ inputs
   - [ ] Document modules/database/ inputs
   - [ ] Create module usage examples

### Priority: PLANNING (Next week)

9. **Quickstart & Examples**
   - [ ] Create autonomous-deploy quickstart.md
   - [ ] Create GitHub Actions workflow templates (YAML skeleton)
   - [ ] Create sample CI/CD architecture diagram

10. **Engineering Handoff**
    - [ ] Create engineering checklist (for Phase 2)
    - [ ] Document what's ready to code
    - [ ] List all decisions made (no more unknowns)

---

## Success Criteria (Phase 1 Planning)

- [x] All 5 key decisions documented and ratified
- [x] Constitution Check passed (all 8 principles addressed)
- [ ] GitHub configuration plan ready (no OIDC setup yet)
- [ ] Terraform variables documented (design ready)
- [ ] Data model defined
- [ ] API contracts written
- [ ] Drop Deploy manifest schema defined
- [ ] Sample app structure planned
- [ ] Documentation structure created
- [ ] Phase 2 engineering checklist ready

---

## Next Steps

### Immediate (Today)

1. ✅ **Decision Review** - Share decisions with team for approval
2. **GitHub Setup** - Team member creates Environments & prepares secrets

### This Week

3. **Variables Implementation** - Add Phase 1 variables to variables.tf
4. **Documentation** - Update DEPLOYMENT_GUIDE.md and create references
5. **Design Documentation** - Create data-model.md and contracts

### Next Week (Phase 2 Engineering)

6. **Implementation Kickoff** - Engineering team begins:
   - GitHub Actions workflow YAML files
   - Backend configuration setup
   - Module implementation
   - Sample app creation
   - CI/CD testing

---

## Risk Assessment

### Phase 1 Planning Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **Decisions reversed mid-engineering** | Medium | High | Get team sign-off now on all 5 decisions |
| **GitHub Actions complexity underestimated** | Medium | Medium | Create workflow templates early, validate YAML |
| **Module design incomplete** | Low | Medium | Review module contracts with team now |
| **Drop Deploy scope creep** | Medium | Medium | Focus on 5 framework templates only |

### Phase 1 Blockers

- ❌ **None** - All tasks are non-engineering/design work
- ✅ Team can start immediately
- ✅ No infrastructure access needed yet

---

## Git Status

**Branch**: `spec/autonomous-deploy`  
**Current**: Planning phase (Phase 1)  
**Next**: Create research.md, data-model.md, contracts/

```bash
# To continue:
git add .specify/features/autonomous-deploy/
git commit -m "plan: autonomous-deploy Phase 1 - Design & configuration (no engineering)"
```

---

**Planning Status**: ✅ **Phase 1 Design Complete**  
**Ready for**: Non-engineering implementation tasks  
**Estimated Timeline**: 1 week (design) + 2 weeks (engineering Phase 2)

