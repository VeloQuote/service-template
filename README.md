# VeloFlow Service Template

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![VeloFlow](https://img.shields.io/badge/VeloFlow-Compatible-green.svg)](https://github.com/VeloQuote/VeloFlow)

**Production-ready template for creating VeloFlow-compatible AWS Lambda services**

This template provides a complete foundation for building Lambda services that integrate with VeloFlow's workflow orchestration platform, including real-time progress updates, standardized event handling, and comprehensive deployment automation.

---

## Overview

This template includes everything you need to create a VeloFlow service:

- ✅ **VeloFlow Integration**: Full compatibility with VeloFlow event format and response contract
- ✅ **Real-time Progress**: EventBridge integration for live progress updates
- ✅ **Multi-stage Support**: Proper handling of `output_key` for complex workflows
- ✅ **GitHub Actions CI/CD**: Trunk-based development with automated testing and deployments (NEW)
- ✅ **Comprehensive Testing**: Unit tests, code quality checks, and security scanning (NEW)
- ✅ **Multiple Deployment Options**: AWS SAM, Serverless Framework, or plain AWS CLI
- ✅ **Production Ready**: Error handling, logging, monitoring, and CloudWatch alarms
- ✅ **Well Documented**: Clear TODOs and examples throughout

---

## Quick Start

### 1. Clone or Copy This Template

```bash
# Copy the template to your new service directory
cp -r service-template my-new-service
cd my-new-service
```

### 2. Customize for Your Service

**Update the following files with your service details:**

1. **`lambda_handler.py`**:
   - Update `SERVICE_ID` constant
   - Replace `process_file()` function with your actual logic
   - Add any custom error handling

2. **`serverless.yml`** or **`template.yaml`**:
   - Update `service` name
   - Update `description`
   - Add any custom environment variables
   - Adjust memory/timeout if needed

3. **`requirements.txt`**:
   - Add your service-specific dependencies

4. **`README.md`**:
   - Replace this template README with your service documentation

### 3. Configure Environment

```bash
# Copy environment template
cp .env.sample .env

# Edit .env and set your values
vim .env
```

### 4. Deploy

Choose your preferred deployment method:

**Option A: Serverless Framework (Recommended)**
```bash
npm install
npm run deploy:dev
```

**Option B: AWS SAM**
```bash
sam build
sam deploy --guided
```

**Option C: Plain AWS CLI Script**
```bash
./deploy_lambda.sh --function-name my-service
```

### 5. Test

```bash
# Update test-event.json with your test data
vim test-event.json

# Invoke the function
aws lambda invoke \
  --function-name my-service-dev \
  --payload file://test-event.json \
  response.json

# Check the response
cat response.json
```

### 6. Register with VeloFlow

```bash
# Update veloflow.json with your service details
vim veloflow.json

# Use VeloFlow's registration script
cd ~/git/VeloFlow
python3 scripts/services/register_service.py ~/path/to/my-service --stage dev
```

The registration script reads your `veloflow.json` metadata file and registers your service in VeloFlow's service registry.

---

## GitHub Actions CI/CD

This template includes a complete trunk-based development workflow with GitHub Actions:

### Workflow Overview

- **PR Validation** (`pr-validation.yml`): Automatic testing, linting, and security scans on pull requests
- **CI Deploy Dev** (`ci-deploy-dev.yml`): Automatic build and deploy to dev on merge to main
- **Promote to QA** (`promote-qa.yml`): Manual promotion of tested artifacts from dev to QA
- **Promote to Prod** (`promote-prod.yml`): Manual promotion with approval from QA to production

### Key Features

- ✅ **Build Once, Deploy Many**: Artifacts are built once and promoted across environments
- ✅ **Git Tag Versioning**: Each deployment creates tags (`build-*`, `qa-*`, `prod-*`)
- ✅ **Automated Testing**: Unit tests, coverage checks, linting, and security scans
- ✅ **Smoke Tests**: Automatic validation after each deployment
- ✅ **Rollback Support**: Easy rollback to previous versions
- ✅ **Release Management**: Automatic GitHub releases for production deployments

### Setup Instructions

1. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   ```
   AWS_ACCESS_KEY_ID - Your AWS access key
   AWS_SECRET_ACCESS_KEY - Your AWS secret key
   ```

2. **Configure GitHub Environments** (Settings → Environments):
   - Create `qa` environment (optional approval)
   - Create `production` environment (required reviewers recommended)

3. **Enable Branch Protection** (Settings → Branches):
   - Require PR approval
   - Require status checks: `validate / Validate PR`
   - Require branches to be up to date

### Usage

**Deploy a feature:**
```bash
# Create PR, get approval, merge to main
# CI automatically deploys to dev
```

**Promote to QA:**
```bash
VERSION=$(git ls-remote --tags origin | grep "build-" | tail -n 1 | sed 's/.*build-//')
gh workflow run promote-qa.yml -f artifact_version=$VERSION
```

**Promote to Production:**
```bash
VERSION=$(git ls-remote --tags origin | grep "qa-" | tail -n 1 | sed 's/.*qa-//')
gh workflow run promote-prod.yml -f artifact_version=$VERSION
```

See [`.github/workflows/README.md`](.github/workflows/README.md) for detailed documentation.

---

## Testing

### Running Tests Locally

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest tests/ --cov --cov-report=term-missing -v

# Check code formatting
black --check .

# Check linting
flake8 .

# Check import sorting
isort --check-only --profile black .

# Run security scans
bandit -r .
safety check
```

### Test Structure

- **`tests/test_lambda_handler.py`**: Comprehensive unit tests for the Lambda handler
  - Event validation tests
  - Output key handling tests
  - Error handling tests
  - Success flow tests

Add your service-specific tests to this file or create new test modules in the `tests/` directory.

---

## Project Structure

```
service-template/
├── lambda_handler.py              # Main Lambda handler (TODO: Customize)
├── service_event_emitter.py       # EventBridge integration (Ready to use)
├── requirements.txt               # Python dependencies (TODO: Add yours)
├── requirements-dev.txt           # Development/testing dependencies (NEW)
├── .env.sample                    # Environment variables template
├── .gitignore                     # Git ignore rules
├── test-event.json                # Sample VeloFlow test event
│
├── .github/workflows/             # GitHub Actions CI/CD (NEW)
│   ├── README.md                  # Detailed workflow documentation
│   ├── pr-validation.yml          # PR testing and validation
│   ├── ci-deploy-dev.yml          # Auto deploy to dev
│   ├── promote-qa.yml             # Manual promote to QA
│   └── promote-prod.yml           # Manual promote to production
│
├── scripts/                       # Utility scripts
│   └── README.md                  # Scripts documentation
│
├── tests/                         # Unit tests (NEW)
│   └── test_lambda_handler.py     # Lambda handler tests
│
├── veloflow.json                  # Service metadata (NEW)
│                                  # Declares capabilities, parameters, constraints
│
├── Deployment Options (Choose one):
├── serverless.yml                 # Serverless Framework config
├── template.yaml                  # AWS SAM template
└── deploy_lambda.sh               # Plain AWS CLI deployment script
│
├── package.json                   # NPM scripts for Serverless
└── README.md                      # This file
```

---

## VeloFlow Integration

### Event Format

Your Lambda receives events in this format:

```json
{
  "invocation_type": "direct",
  "job_id": "a2df38da-edd6-4c75-b90f-4114f3cf1edf",
  "input_bucket": "veloflow-dev-input",
  "input_key": "uploads/user123/document.pdf",
  "output_bucket": "veloflow-dev-output",
  "output_key": "jobs/a2df38da/stage-1/output.xlsx",
  "reference_date": "2025-01-15",
  "customer_tier": "standard",
  "stage_config": {
    "custom_param": "value"
  }
}
```

### Response Format

Return responses in this format:

**Success:**
```json
{
  "status": "success",
  "output_bucket": "veloflow-dev-output",
  "output_key": "jobs/a2df38da/stage-1/output.xlsx",
  "metadata": {
    "processing_time_ms": 1234,
    "custom_metric": "value"
  }
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Description of what went wrong",
  "error_type": "ProcessingError",
  "metadata": {
    "job_id": "a2df38da-edd6-4c75-b90f-4114f3cf1edf"
  }
}
```

### Real-time Progress Updates

Use the `ServiceEventEmitter` to send real-time updates:

```python
from service_event_emitter import ServiceEventEmitter

emitter = ServiceEventEmitter(
    job_id=job_id,
    service_id='my-service-v1',
    stage_id=stage_config.get('stage_id')
)

# Emit progress
emitter.emit_progress('Processing file...')

# Emit success
emitter.emit_success(
    'Processing completed',
    output_key=output_key,
    metadata={'records': 100}
)

# Emit error
emitter.emit_error(
    'Processing failed',
    error_type='ValidationError'
)
```

### Output Key Handling (CRITICAL)

**Always use the `output_key` provided in the event:**

```python
# ✅ Correct - Use provided output_key
output_key = event.get('output_key')
if not output_key:
    # Fallback for legacy single-stage workflows
    output_key = f"jobs/{job_id}/output.xlsx"

# Upload to the exact key provided
s3_client.upload_file(result_file, output_bucket, output_key)

# Return the same key in response
return {
    'status': 'success',
    'output_bucket': output_bucket,
    'output_key': output_key  # Must match what was provided
}
```

---

## Customization Guide

### 1. Service Logic

Edit `lambda_handler.py` and replace the `process_file()` function:

```python
def process_file(
    input_path: Path,
    output_path: Path,
    config: Dict[str, Any],
    emitter: ServiceEventEmitter
) -> Dict[str, Any]:
    """
    TODO: Implement your service logic here
    """
    # Your processing logic
    emitter.emit_progress('Step 1 of 3: Parsing...')
    # ... do work ...

    emitter.emit_progress('Step 2 of 3: Processing...')
    # ... do work ...

    emitter.emit_progress('Step 3 of 3: Finalizing...')
    # ... do work ...

    return {
        'success': True,
        'metadata': {
            'records_processed': 100
        }
    }
```

### 2. Dependencies

Add your dependencies to `requirements.txt`:

```txt
boto3>=1.34.0
openpyxl>=3.1.0      # For Excel processing
pillow>=10.0.0       # For image processing
anthropic>=0.18.0    # For AI services
```

### 3. Environment Variables

Add custom environment variables in:
- `.env.sample` (for local development)
- `serverless.yml` (under `provider.environment`)
- `template.yaml` (under `Environment.Variables`)

### 4. IAM Permissions

If your service needs additional AWS permissions, update:

**Serverless Framework (`serverless.yml`):**
```yaml
provider:
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - dynamodb:GetItem
          Resource:
            - arn:aws:dynamodb:*:*:table/my-table
```

**AWS SAM (`template.yaml`):**
```yaml
Policies:
  - DynamoDBReadPolicy:
      TableName: my-table
```

### 5. Memory and Timeout

Adjust based on your service needs:

- Light processing: 1024 MB, 300s timeout
- Medium processing: 2048 MB, 600s timeout
- Heavy processing: 3008 MB, 900s timeout

Update in `serverless.yml` or `template.yaml`.

---

## Deployment Options

### Option 1: Serverless Framework (Recommended)

**Pros:**
- Simple configuration
- Built-in stage management
- Easy to add plugins
- Great for iterative development

**Setup:**
```bash
npm install
```

**Deploy:**
```bash
# Development
npm run deploy:dev

# Staging
npm run deploy:staging

# Production
npm run deploy:prod
```

**View Logs:**
```bash
npm run logs:dev
```

**Remove:**
```bash
npm run remove:dev
```

### Option 2: AWS SAM

**Pros:**
- Native AWS CloudFormation
- Local testing support
- Good IDE integration
- Infrastructure as Code

**Setup:**
```bash
# Install AWS SAM CLI
# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
```

**Deploy:**
```bash
# Build
sam build

# Deploy (first time with guided setup)
sam deploy --guided

# Subsequent deploys
sam deploy
```

**Local Testing:**
```bash
sam local invoke -e test-event.json
```

### Option 3: Plain AWS CLI Script

**Pros:**
- No additional tools needed
- Full control over deployment
- Good for CI/CD pipelines

**Deploy:**
```bash
./deploy_lambda.sh --function-name my-service-dev --region us-east-1
```

**Test:**
```bash
aws lambda invoke \
  --function-name my-service-dev \
  --payload file://test-event.json \
  response.json
```

---

## Testing

### Local Testing

```python
# Run the handler locally
python lambda_handler.py
```

### Lambda Console Testing

1. Go to AWS Lambda Console
2. Select your function
3. Create a test event with VeloFlow format
4. Click "Test"

### Integration Testing

```bash
# Invoke with test event
aws lambda invoke \
  --function-name my-service-dev \
  --payload file://test-event.json \
  response.json

# Check response
cat response.json | jq
```

---

## Monitoring

### CloudWatch Logs

```bash
# Using Serverless
npm run logs:dev

# Using AWS CLI
aws logs tail /aws/lambda/my-service-dev --follow
```

### CloudWatch Metrics

Monitor these key metrics:
- **Invocations**: Total executions
- **Errors**: Failed executions
- **Duration**: Processing time
- **Throttles**: Rate limiting

### CloudWatch Alarms

The template includes pre-configured alarms:
- **Error Alarm**: Triggers when error count > 5 in 5 minutes
- **Duration Alarm**: Triggers when avg duration > 10 minutes

---

## VeloFlow Integration Checklist

Before registering with VeloFlow, ensure:

- [ ] Lambda function accepts VeloFlow event format
- [ ] Function returns standardized response format
- [ ] `output_key` from event is used (not hardcoded)
- [ ] `ServiceEventEmitter` is initialized with correct `service_id`
- [ ] Progress events are emitted at key checkpoints
- [ ] Success event is emitted with `output_key`
- [ ] Error events are emitted on failures
- [ ] IAM permissions include EventBridge PutEvents
- [ ] Environment variable `EVENT_BUS_NAME` is set correctly
- [ ] S3 read permissions for input buckets
- [ ] S3 write permissions for output buckets
- [ ] Function timeout is appropriate (recommended: 900s)
- [ ] Function memory is sufficient (recommended: 3008 MB)
- [ ] CloudWatch Logs are configured
- [ ] Function has been tested with sample event

---

## Troubleshooting

### Issue: "Missing required field: job_id"

**Cause**: Event format is incorrect

**Fix**: Ensure test event includes all required fields:
- `invocation_type`: "direct"
- `job_id`
- `input_bucket`
- `input_key`
- `output_bucket`

### Issue: "Access Denied" on S3

**Cause**: Missing IAM permissions

**Fix**: Verify Lambda execution role has:
- `s3:GetObject` on input buckets
- `s3:PutObject` on output buckets

### Issue: Progress events not appearing

**Cause**: EventBridge permissions or configuration issue

**Fix**:
1. Check `EVENT_BUS_NAME` environment variable
2. Verify IAM role has `events:PutEvents` permission
3. Confirm event bus name matches VeloFlow stage

### Issue: "No space left on device"

**Cause**: Ephemeral storage exceeded

**Fix**: Increase ephemeral storage in configuration:
```yaml
ephemeralStorageSize: 4096  # Increase to 4GB
```

### Issue: Lambda timeout

**Cause**: Processing takes longer than timeout

**Fix**: Increase timeout:
```yaml
timeout: 900  # Maximum 15 minutes
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:
```python
try:
    result = process_file(...)
except SpecificError as e:
    emitter.emit_error(str(e), error_type='SpecificError')
    return create_error_response(e)
```

### 2. Logging

Use structured logging:
```python
print(f"Processing job {job_id}")
print(f"Input: s3://{input_bucket}/{input_key}")
print(f"Status: Processing completed in {duration_ms}ms")
```

### 3. Cleanup

Always cleanup temporary files:
```python
try:
    local_input_path.unlink()
    local_output_path.unlink()
except Exception as e:
    print(f"Warning: Failed to cleanup: {e}")
```

### 4. Progress Updates

Emit progress at meaningful checkpoints:
```python
emitter.emit_progress('Downloading input...')      # 0-20%
emitter.emit_progress('Processing data...')        # 20-80%
emitter.emit_progress('Uploading output...')       # 80-100%
emitter.emit_success('Complete', output_key=key)   # 100%
```

### 5. Metadata

Return useful metadata:
```python
metadata = {
    'processing_time_ms': duration,
    'input_size_bytes': input_size,
    'output_size_bytes': output_size,
    'records_processed': record_count,
    'service_version': SERVICE_VERSION
}
```

---

## Related Documentation

- [VeloFlow Integration Guide](~/git/VeloFlow/VELOFLOW_INTEGRATION_GUIDE.md)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)

---

## Support

For issues or questions:

1. Review this README thoroughly
2. Check the VeloFlow integration guide
3. Review CloudWatch logs for errors
4. Contact the VeloQuote team

---

## License

Proprietary - VeloQuote

---

## Changelog

### v1.0.0 (2025-11-14) - Initial Template

- Complete VeloFlow-compatible Lambda handler
- Real-time progress event integration
- Multiple deployment options (Serverless, SAM, CLI)
- Comprehensive documentation
- Production-ready configuration

---

**Last Updated**: 2025-11-14
**Maintainer**: VeloQuote Team
