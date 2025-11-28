# GitHub Actions Workflows - Trunk-Based Development

This directory contains the GitHub Actions workflows for VeloFlow services, implementing a trunk-based development approach with build artifact promotion.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Developer → Create Pull Request                            │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  PR Validation (AUTOMATIC)                                  │
│  • Run tests, linting, security scans                       │
│  • Validate configuration                                   │
│  • Block merge if fails                                     │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Merge to main → CI Build & Deploy to Dev (AUTOMATIC)      │
│  • Build artifact                                           │
│  • Store in GitHub Artifacts                                │
│  • Deploy to DEV                                            │
│  • Create build tag                                         │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Promote to QA (MANUAL)                                     │
│  • Download artifact (no rebuild)                           │
│  • Deploy to QA                                             │
│  • Run smoke tests                                          │
│  • Create QA tag                                            │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Promote to Production (MANUAL + APPROVAL)                  │
│  • Verify QA tag exists                                     │
│  • Download artifact                                        │
│  • Deploy to PROD                                           │
│  • Create production tag & release                          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Workflow Files

### 1. `pr-validation.yml` - PR Validation (Automatic)

**Trigger:** Pull requests to `main` branch

**Purpose:** Validate code quality before merge

**Steps:**
- ✅ Run unit tests with coverage (40% minimum)
- ✅ Check code formatting (black)
- ✅ Check code quality (flake8)
- ✅ Check import sorting (isort)
- ✅ Security scan (bandit, safety)
- ✅ Validate serverless configuration
- ✅ Check for hardcoded secrets

**Branch Protection:** Configure `main` branch to require this check to pass before merge.

### 2. `ci-deploy-dev.yml` - CI Build and Deploy to Dev (Automatic)

**Trigger:** Push to `main` branch (after PR merge)

**Purpose:** Build once, deploy to dev, create artifact for promotion

**Steps:**
1. Generate version: `{git-sha}-{timestamp}` (e.g., `84fb588-20250120-143022`)
2. Run tests to ensure code quality
3. Build deployment package with Serverless Framework
4. Create artifact tarball with source code
5. Upload to GitHub Artifacts (90-day retention)
6. Deploy to Dev environment
7. Update service registry in DynamoDB (optional)
8. Run smoke test on dev
9. Create `build-{version}` git tag

**Artifact Contents:**
- `serverless.yml` - Configuration
- `lambda_handler.py` - Handler code
- `service_event_emitter.py` - Event emitter
- Other source files (customize based on your service)

**Output:** Build tag created, artifact stored, dev environment updated

### 3. `promote-qa.yml` - Promote to QA (Manual)

**Trigger:** Manual workflow dispatch with `artifact_version` input

**Purpose:** Promote tested artifact from dev to QA

**Prerequisites:**
- Build tag `build-{version}` must exist
- Artifact must be available in GitHub Artifacts

**Steps:**
1. Validate build tag exists
2. Download pre-built artifact (no rebuild!)
3. Extract artifact
4. Package for QA stage
5. Deploy to QA using pre-built package
6. Update service registry (optional)
7. Upload test file
8. Run smoke test
9. Create `qa-{version}` git tag

**Usage:**
```bash
# Get latest build version
VERSION=$(git ls-remote --tags origin | grep "build-" | tail -n 1 | sed 's/.*build-//')

# Promote to QA
gh workflow run promote-qa.yml -f artifact_version=$VERSION
```

**Environment:** Configure `qa` environment in GitHub settings (optional approval)

### 4. `promote-prod.yml` - Promote to Production (Manual + Approval)

**Trigger:** Manual workflow dispatch with inputs

**Purpose:** Promote QA-tested artifact to production

**Prerequisites:**
- QA tag `qa-{version}` must exist (enforced)
- Build tag `build-{version}` must exist
- Artifact must be available in GitHub Artifacts

**Inputs:**
- `artifact_version` (required) - Version to deploy
- `deployment_notes` (optional) - Release notes
- `skip_tests` (optional) - Skip smoke tests (emergency rollback only)

**Steps:**
1. Validate QA tag exists (ensures QA testing)
2. Download pre-built artifact
3. Create backup of current production version
4. Deploy to Production
5. Update service registry (optional)
6. Run smoke test (unless skipped)
7. Create `prod-{version}` git tag
8. Create GitHub Release

**Usage:**
```bash
# Get QA version
VERSION=$(git ls-remote --tags origin | grep "qa-" | tail -n 1 | sed 's/.*qa-//')

# Promote to production
gh workflow run promote-prod.yml \
  -f artifact_version=$VERSION \
  -f deployment_notes="Production deployment notes"
```

**Environment:** Configure `production` environment with required reviewers

## 🏷️ Git Tags and Versioning

### Version Format

`{git-sha}-{timestamp}`

Example: `84fb588-20250120-143022`
- `84fb588` - First 8 characters of git commit SHA
- `20250120` - Date (YYYYMMDD)
- `143022` - Time (HHMMSS)

### Tag Lifecycle

1. **`build-{version}`** - Created when artifact is built and deployed to dev
2. **`qa-{version}`** - Created when artifact is deployed to QA
3. **`prod-{version}`** - Created when artifact is deployed to production

### Querying Tags

```bash
# List all build tags
git ls-remote --tags origin | grep "build-"

# List all QA deployments
git ls-remote --tags origin | grep "qa-"

# List all production deployments
git ls-remote --tags origin | grep "prod-"

# Get latest production version
git ls-remote --tags origin | grep "prod-" | tail -n 1
```

## 📦 Artifact Management

### Artifact Naming

`service-{service-name}-{version}.tar.gz`

Example: `service-your-service-84fb588-20250120-143022.tar.gz`

### Retention

- GitHub Artifacts: 90 days
- After 90 days, artifacts are deleted automatically
- Git tags remain forever for audit trail

### Finding Artifacts

1. Go to GitHub Actions tab
2. Click on "CI - Build and Deploy to Dev" workflow
3. Click on a successful run
4. Scroll to "Artifacts" section at bottom
5. Download artifact

Or use GitHub CLI:
```bash
gh run list --workflow=ci-deploy-dev.yml --limit 10
gh run view <RUN_ID>
gh run download <RUN_ID>
```

## 🚀 Common Workflows

### Deploy a New Feature

```bash
# 1. Create feature branch from main
git checkout main
git pull
git checkout -b feature-new-feature

# 2. Make changes and commit
git add .
git commit -m "Add new feature"
git push origin feature-new-feature

# 3. Create pull request
gh pr create --base main --title "Add new feature"

# 4. Wait for PR validation to pass
# 5. Get approval and merge

gh pr merge --merge

# 6. CI automatically builds and deploys to dev
# Wait for "CI - Build and Deploy to Dev" workflow to complete

# 7. Check dev deployment
aws lambda invoke \
  --function-name veloflow-dev-{service-name} \
  --payload file://test-event.json \
  response.json
```

### Promote to QA

```bash
# 1. Get latest build version
VERSION=$(git ls-remote --tags origin | grep "build-" | tail -n 1 | sed 's/.*build-//')
echo "Latest version: $VERSION"

# 2. Promote to QA
gh workflow run promote-qa.yml -f artifact_version=$VERSION

# 3. Monitor workflow
gh run watch

# 4. Verify QA deployment
aws lambda invoke \
  --function-name veloflow-qa-{service-name} \
  --payload file://test-event.json \
  response.json
```

### Promote to Production

```bash
# 1. Get QA-tested version
VERSION=$(git ls-remote --tags origin | grep "qa-" | tail -n 1 | sed 's/.*qa-//')
echo "QA version: $VERSION"

# 2. Promote to production with deployment notes
gh workflow run promote-prod.yml \
  -f artifact_version=$VERSION \
  -f deployment_notes="
## Changes
- Add new feature
- Improve error handling
- Update dependencies

## Testing
- ✅ Unit tests passing
- ✅ Dev smoke test passed
- ✅ QA smoke test passed
- ✅ Manual testing completed
"

# 3. Approve deployment (if required reviewers configured)
# Go to Actions tab, find the workflow run, and approve

# 4. Monitor deployment
gh run watch

# 5. Verify production
aws lambda invoke \
  --function-name veloflow-prod-{service-name} \
  --payload file://test-event.json \
  response.json
```

### Rollback Production

```bash
# 1. Find previous production version
git ls-remote --tags origin | grep "prod-" | tail -n 5

# 2. Select previous version (e.g., second to last)
PREV_VERSION=$(git ls-remote --tags origin | grep "prod-" | tail -n 2 | head -n 1 | sed 's/.*prod-//')
echo "Rolling back to: $PREV_VERSION"

# 3. Rollback (skip tests for speed)
gh workflow run promote-prod.yml \
  -f artifact_version=$PREV_VERSION \
  -f skip_tests=true \
  -f deployment_notes="Rollback due to issue in production"

# 4. Monitor rollback
gh run watch
```

## 🔐 Required Secrets

Configure these secrets in GitHub repository settings (Settings → Secrets and variables → Actions):

### AWS Credentials
- **AWS_ACCESS_KEY_ID** - AWS access key with deployment permissions
- **AWS_SECRET_ACCESS_KEY** - AWS secret access key

### Required Permissions

The AWS credentials need the following permissions:
- **Lambda:** Full access to create/update functions
- **S3:** Read/write access to deployment buckets
- **IAM:** PassRole for Lambda execution role
- **CloudFormation:** Create/update stacks (for Serverless Framework)
- **DynamoDB:** Read/write to service registry table (optional)
- **EventBridge:** PutEvents for progress updates

## 🌳 Environment Configuration

### GitHub Environments

Configure these in Settings → Environments:

#### QA Environment
- **Protection rules:** Optional (can add required reviewers if desired)
- **Environment secrets:** None (uses repository secrets)
- **Deployment branches:** Any branch (workflow dispatch only)

#### Production Environment
- **Protection rules:**
  - ✅ Required reviewers (add team members)
  - ✅ Wait timer: 5 minutes (optional)
- **Environment secrets:** None (uses repository secrets)
- **Deployment branches:** Any branch (workflow dispatch only)

### Branch Protection Rules

Configure for `main` branch (Settings → Branches → Branch protection rules):

- ✅ Require pull request before merging
- ✅ Require approvals: 1
- ✅ Require status checks to pass before merging:
  - `validate / Validate PR` (from pr-validation.yml)
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

## 📊 Monitoring and Logs

### View Workflow Runs

```bash
# List recent workflow runs
gh run list --limit 20

# View specific workflow runs
gh run list --workflow=ci-deploy-dev.yml
gh run list --workflow=promote-qa.yml
gh run list --workflow=promote-prod.yml

# View logs for a run
gh run view <RUN_ID> --log

# Watch a running workflow
gh run watch
```

### View Lambda Logs

```bash
# Dev logs
aws logs tail /aws/lambda/veloflow-dev-{service-name} --follow

# QA logs
aws logs tail /aws/lambda/veloflow-qa-{service-name} --follow

# Production logs
aws logs tail /aws/lambda/veloflow-prod-{service-name} --follow
```

### Check Service Registry (if using)

```bash
# Verify service registration
python scripts/update_service_registry.py --stage dev --verify-only
python scripts/update_service_registry.py --stage qa --verify-only
python scripts/update_service_registry.py --stage prod --verify-only
```

## 🐛 Troubleshooting

### Workflow Failed: "Build tag not found"

**Problem:** Trying to promote an artifact that doesn't exist.

**Solution:**
```bash
# List available build tags
git ls-remote --tags origin | grep "build-"

# Use a valid version from the list
gh workflow run promote-qa.yml -f artifact_version=<VALID_VERSION>
```

### Workflow Failed: "Artifact not found"

**Problem:** Artifact expired (90-day retention) or was not created.

**Solution:**
```bash
# Re-run CI to create new artifact
# Make a trivial commit to trigger CI
git commit --allow-empty -m "Rebuild artifact"
git push origin main

# Or cherry-pick the commit and rebuild
git checkout main
git cherry-pick <COMMIT_SHA>
git push origin main
```

### Workflow Failed: "QA tag not found"

**Problem:** Trying to deploy to production without QA testing.

**Solution:**
```bash
# Deploy to QA first
VERSION=<YOUR_VERSION>
gh workflow run promote-qa.yml -f artifact_version=$VERSION

# Wait for QA deployment to complete
gh run watch

# Then deploy to production
gh workflow run promote-prod.yml -f artifact_version=$VERSION
```

### Smoke Test Failed

**Problem:** Lambda invocation failed or returned error.

**Solution:**
1. Check Lambda logs:
   ```bash
   aws logs tail /aws/lambda/veloflow-<stage>-{service-name} --since 10m
   ```

2. Verify test file exists (if using):
   ```bash
   aws s3 ls s3://veloflow-<stage>-output/test/
   ```

3. Test manually:
   ```bash
   aws lambda invoke \
     --function-name veloflow-<stage>-{service-name} \
     --payload file://test-event.json \
     response.json
   cat response.json | jq '.'
   ```

## 📚 Additional Resources

- [VeloFlow Integration Guide](../../README.md)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

## 🔄 Customization for Your Service

When customizing these workflows for a new service:

1. **Update service name references** in all workflow files
   - Replace placeholder names with your actual service name
   - Update function names (e.g., `veloflow-{stage}-your-service`)

2. **Customize artifact contents** in `ci-deploy-dev.yml`
   - Add/remove files based on your service structure
   - Include any additional directories or configuration files

3. **Adjust test file paths** (if using smoke tests)
   - Update S3 paths for test files
   - Modify test-event.json as needed

4. **Update service registry script** (if using)
   - Modify `scripts/update_service_registry.py` with your service details

5. **Configure GitHub secrets and environments**
   - Add AWS credentials
   - Set up QA and production environments
   - Configure branch protection rules

---

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
