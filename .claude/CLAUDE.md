# VeloFlow Service Template - Claude Instructions

This is a **template repository** for creating VeloFlow-compatible Lambda services. When customizing this template for a new service, follow these instructions carefully.

---

## Template Overview

This template provides a production-ready foundation for VeloFlow Lambda services with:
- Complete VeloFlow event handling
- Real-time progress updates via EventBridge
- **GitHub Actions CI/CD with trunk-based development** (NEW)
- **Comprehensive testing infrastructure** (pytest, coverage, linting, security scans) (NEW)
- Multiple deployment options (Serverless Framework, AWS SAM, plain AWS CLI)
- Comprehensive error handling
- S3 integration for input/output files
- CloudWatch monitoring and alarms
- **Service metadata file (veloflow.json)** (NEW)

### New CI/CD Features

The template now includes:
- **`.github/workflows/`**: Complete GitHub Actions workflows for CI/CD
  - `pr-validation.yml`: Automatic testing and validation on pull requests
  - `ci-deploy-dev.yml`: Automatic build and deploy to dev on merge to main
  - `promote-qa.yml`: Manual promotion from dev to QA
  - `promote-prod.yml`: Manual promotion from QA to production
- **`requirements-dev.txt`**: Testing and development dependencies
- **`veloflow.json`**: Service metadata for VeloFlow registration
- **`tests/test_lambda_handler.py`**: Comprehensive unit tests

---

## When Customizing This Template

### Step 1: Service Identification

**ALWAYS ask the user for these details first:**

1. **Service Name** (e.g., "pdf-to-json", "image-analyzer", "data-validator")
   - Used in: serverless.yml, template.yaml, package.json, deploy_lambda.sh
   - Format: lowercase-with-hyphens

2. **Service ID** (e.g., "pdf-to-json-v1", "image-analyzer-v1")
   - Used in: lambda_handler.py (SERVICE_ID constant)
   - Format: service-name-v1

3. **Service Description** (e.g., "Converts PDF documents to structured JSON")
   - Used in: serverless.yml, template.yaml, README.md

4. **Input File Type** (e.g., PDF, Excel, Image, JSON)
   - Affects: Validation logic in lambda_handler.py

5. **Output File Type** (e.g., Excel, JSON, PDF, CSV)
   - Affects: output_key default extension in lambda_handler.py
   - Affects: S3 upload ContentType

6. **Processing Requirements**:
   - External APIs needed? (e.g., Anthropic, OpenAI)
   - Python libraries needed? (e.g., openpyxl, pillow, pandas)
   - Estimated processing time? (affects timeout settings)
   - Memory requirements? (default is 3008MB)

### Step 2: Critical Files to Update

**MANDATORY Updates (Must do for every service):**

1. **lambda_handler.py**:
   - Line 52: `SERVICE_ID = "your-service-v1"` → Update with actual service ID
   - Line 53: `SERVICE_VERSION = "1.0.0"` → Keep or update
   - Line 98: Update output file extension (`.xlsx` → `.json`, `.pdf`, etc.)
   - Lines 245-280: Replace `process_file()` function with actual service logic
   - Add input validation if needed (file type, size limits)

2. **serverless.yml** (if using Serverless Framework):
   - Line 2: `service: veloflow-service-template` → Update service name
   - Line 20: `SERVICE_ID: service-template-v1` → Update service ID
   - Line 78: `description:` → Update with service description
   - Lines 20-23: Add any service-specific environment variables

3. **template.yaml** (if using AWS SAM):
   - Line 6-8: Update `ServiceName` default value
   - Line 45: `SERVICE_ID:` → Update service ID
   - Line 35: `FunctionName:` uses ServiceName parameter
   - Add service-specific parameters if needed (API keys, etc.)

4. **requirements.txt**:
   - Add all service-specific Python dependencies
   - Keep `boto3>=1.34.0` (required for AWS SDK)

5. **package.json**:
   - Line 2: `"name": "veloflow-service-template"` → Update service name
   - Line 4: `"description":` → Update description

6. **deploy_lambda.sh**:
   - Line 16: `FUNCTION_NAME="veloflow-service-template"` → Update default name
   - Line 136: Update zip command if adding custom modules/directories

7. **.env.sample**:
   - Lines 9-10: Update SERVICE_ID and SERVICE_VERSION
   - Add any service-specific environment variables

### Step 3: Implement Processing Logic

**The `process_file()` function (lambda_handler.py, lines 245-280) MUST be replaced.**

**Key requirements for the implementation:**

1. **Function Signature** (DO NOT change):
   ```python
   def process_file(
       input_path: Path,
       output_path: Path,
       config: Dict[str, Any],
       emitter: ServiceEventEmitter
   ) -> Dict[str, Any]:
   ```

2. **Must emit progress at key checkpoints**:
   ```python
   emitter.emit_progress('Step 1: Analyzing input...')
   # ... do work ...
   emitter.emit_progress('Step 2: Processing data...')
   # ... do work ...
   emitter.emit_progress('Step 3: Generating output...')
   ```

3. **Must write output file to `output_path`**:
   - The handler expects a file at `output_path` to upload to S3
   - Make sure the file exists before returning

4. **Must return a dictionary with metadata**:
   ```python
   return {
       'success': True,
       'metadata': {
           'records_processed': 100,
           'processing_time_ms': 1234,
           # Add service-specific metrics
       }
   }
   ```

5. **Raise exceptions for errors** (don't return error status):
   - The handler will catch exceptions and create proper error responses
   - Use specific exception types when possible (ValueError, FileNotFoundError, etc.)

### Step 4: Configuration Adjustments

**Memory and Timeout Settings:**

Based on processing requirements, update in serverless.yml or template.yaml:

- **Light processing** (< 1 minute): 1024 MB, 300s timeout
- **Medium processing** (1-5 minutes): 2048 MB, 600s timeout
- **Heavy processing** (5-15 minutes): 3008 MB, 900s timeout

**Ephemeral Storage:**

Default is 2048 MB. Increase if handling large files:
- Standard files (< 100 MB): 2048 MB
- Large files (100-500 MB): 4096 MB
- Very large files (> 500 MB): 10240 MB (max)

### Step 5: IAM Permissions

**Default permissions included:**
- ✅ S3 GetObject (veloflow-*-input, veloflow-*-processing)
- ✅ S3 PutObject (veloflow-*-processing, veloflow-*-output)
- ✅ EventBridge PutEvents (veloflow-*-event-bus)
- ✅ CloudWatch Logs
- ✅ KMS Decrypt (for encrypted environment variables)

**Add additional permissions if service needs:**

**For DynamoDB:**
```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:PutItem
    - dynamodb:Query
  Resource:
    - arn:aws:dynamodb:*:*:table/your-table-name
```

**For Secrets Manager:**
```yaml
- Effect: Allow
  Action:
    - secretsmanager:GetSecretValue
  Resource:
    - arn:aws:secretsmanager:*:*:secret:your-secret-name-*
```

**For Additional S3 Buckets:**
```yaml
- Effect: Allow
  Action:
    - s3:GetObject
  Resource:
    - arn:aws:s3:::your-custom-bucket/*
```

**Important Notes:**
- **KMS Permissions**: Required if your Lambda uses encrypted environment variables (common for API keys). Already included in serverless.yml and template.yaml.
- **Alternative to Custom Role**: You can use VeloFlow's shared IAM role instead of creating service-specific roles. See VeloFlow documentation for details.

---

## VeloFlow Integration Requirements

### CRITICAL: Output Key Handling

**NEVER hardcode the output key format.** Always use the provided `output_key`:

```python
# ✅ CORRECT
output_key = event.get('output_key')
if not output_key:
    # Fallback for legacy single-stage workflows
    output_key = f"jobs/{job_id}/output.xlsx"  # Use appropriate extension

# Upload to the exact key provided
s3_client.upload_file(str(output_path), output_bucket, output_key)

# Return the same key in response
return {
    'status': 'success',
    'output_bucket': output_bucket,
    'output_key': output_key  # MUST match what was provided
}
```

```python
# ❌ WRONG - This breaks multi-stage workflows
output_key = f"jobs/{job_id}/output.xlsx"  # Never hardcode!
```

### Event Format Validation

**The handler already validates these required fields:**
- `invocation_type` (must be "direct")
- `job_id`
- `input_bucket`
- `input_key`
- `output_bucket`

**Optional fields available:**
- `output_key` (MUST use if provided)
- `reference_date`
- `customer_tier`
- `stage_config` (dict with custom parameters)

### Progress Event Guidelines

**Emit progress at meaningful checkpoints (not too frequent):**

```python
# ✅ GOOD - 4-6 progress events for typical workflow
emitter.emit_progress('Starting analysis...')
emitter.emit_progress('Processing page 1 of 10...')
emitter.emit_progress('Processing page 5 of 10...')
emitter.emit_progress('Processing page 10 of 10...')
emitter.emit_progress('Finalizing output...')
```

```python
# ❌ BAD - Too many events
for i in range(1000):
    emitter.emit_progress(f'Processing row {i}...')  # Don't do this!
```

**Rate limit: Maximum 1 event per second**

### Response Format

**Success response (handler creates this automatically):**
```json
{
  "status": "success",
  "output_bucket": "veloflow-dev-output",
  "output_key": "jobs/{job_id}/stage-1/output.xlsx",
  "metadata": {
    "processing_time_ms": 1234,
    "input_file_size_bytes": 5678,
    "output_file_size_bytes": 9012,
    "service_version": "1.0.0",
    "custom_metrics": {}
  }
}
```

**Error response (handler creates this automatically when exceptions occur):**
```json
{
  "status": "error",
  "error": "Description of what went wrong",
  "error_type": "ProcessingError",
  "metadata": {
    "job_id": "...",
    "processing_time_ms": 1234
  }
}
```

### Service Completion Detection

**IMPORTANT:** VeloFlow detects service completion through **S3 bucket notifications**, not EventBridge events.

- When your service writes the output file to S3, the orchestrator automatically detects it via S3 notifications
- EventBridge progress events (`service.progress`, `service.completed`, `service.failed`) are for real-time UI updates only
- **You do NOT need to signal completion** - just upload the output file to the correct S3 key
- The orchestrator will automatically proceed to the next workflow stage

**What this means for your service:**
1. Upload output file to the exact `output_key` provided in the event
2. Emit progress events throughout processing for user visibility
3. Return success response from Lambda (for logging/debugging)
4. VeloFlow automatically detects the S3 upload and continues the workflow

**Troubleshooting:** If workflows appear stuck after your service completes, verify:
- Output file exists at the correct S3 key
- S3 bucket notifications are configured correctly in VeloFlow infrastructure
- Check VeloFlow orchestrator logs for S3 event processing

---

## Common Service Patterns

### Pattern 1: PDF Processing Service

**Dependencies:**
```txt
boto3>=1.34.0
pypdf2>=3.0.0
pillow>=10.0.0
```

**Processing logic:**
```python
def process_file(input_path, output_path, config, emitter):
    emitter.emit_progress('Extracting text from PDF...')
    # Extract text/images from PDF

    emitter.emit_progress('Processing extracted content...')
    # Process the content

    emitter.emit_progress('Generating output...')
    # Create output file

    return {'success': True, 'metadata': {'pages': 10}}
```

### Pattern 2: Excel Processing Service

**Dependencies:**
```txt
boto3>=1.34.0
openpyxl>=3.1.0
pandas>=2.0.0
```

**Processing logic:**
```python
def process_file(input_path, output_path, config, emitter):
    import openpyxl
    import pandas as pd

    emitter.emit_progress('Reading Excel file...')
    df = pd.read_excel(input_path)

    emitter.emit_progress('Processing data...')
    # Process dataframe

    emitter.emit_progress('Writing output...')
    df.to_excel(output_path, index=False)

    return {'success': True, 'metadata': {'rows': len(df)}}
```

### Pattern 3: AI/Claude Processing Service

**Dependencies:**
```txt
boto3>=1.34.0
anthropic>=0.18.0
```

**Environment variables (.env.sample):**
```
ANTHROPIC_API_KEY=your-key-here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

**Processing logic:**
```python
def process_file(input_path, output_path, config, emitter):
    import anthropic
    import os

    emitter.emit_progress('Initializing Claude API...')
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    emitter.emit_progress('Reading input file...')
    with open(input_path, 'rb') as f:
        content = f.read()

    emitter.emit_progress('Sending to Claude for processing...')
    # Call Claude API

    emitter.emit_progress('Writing results...')
    with open(output_path, 'wb') as f:
        f.write(result)

    return {'success': True, 'metadata': {'tokens_used': 1234}}
```

### Pattern 4: Image Processing Service

**Dependencies:**
```txt
boto3>=1.34.0
pillow>=10.0.0
```

**Processing logic:**
```python
def process_file(input_path, output_path, config, emitter):
    from PIL import Image

    emitter.emit_progress('Loading image...')
    img = Image.open(input_path)

    emitter.emit_progress('Processing image...')
    # Resize, crop, filter, etc.

    emitter.emit_progress('Saving output...')
    img.save(output_path)

    return {
        'success': True,
        'metadata': {
            'original_size': f'{img.size[0]}x{img.size[1]}',
            'format': img.format
        }
    }
```

---

## Testing and Validation

### Before Deployment

1. **Update test-event.json** with appropriate test data:
   ```json
   {
     "invocation_type": "direct",
     "job_id": "test-job-123",
     "input_bucket": "veloflow-dev-input",
     "input_key": "test/sample.pdf",
     "output_bucket": "veloflow-dev-output",
     "customer_tier": "standard",
     "stage_config": {}
   }
   ```

2. **Ensure test file exists in S3**:
   ```bash
   aws s3 cp test-file.pdf s3://veloflow-dev-input/test/sample.pdf
   ```

3. **Local testing** (if possible):
   ```python
   python lambda_handler.py
   ```

### After Deployment

1. **Invoke with test event**:
   ```bash
   aws lambda invoke \
     --function-name service-name-dev \
     --payload file://test-event.json \
     response.json

   cat response.json | jq
   ```

2. **Check CloudWatch logs**:
   ```bash
   aws logs tail /aws/lambda/service-name-dev --follow
   ```

3. **Verify S3 output**:
   ```bash
   aws s3 ls s3://veloflow-dev-output/jobs/test-job-123/
   ```

4. **Test progress events** (check EventBridge):
   ```bash
   aws events put-targets \
     --rule veloflow-dev-service-events \
     --targets "Id"="1","Arn"="..."
   ```

---

## Deployment Methods

### Method 1: Serverless Framework (Recommended)

**Use when:**
- Iterative development
- Multiple stages (dev/staging/prod)
- Team development

**Commands:**
```bash
npm install
npm run deploy:dev    # Deploy to dev
npm run logs:dev      # View logs
npm run remove:dev    # Remove deployment
```

### Method 2: AWS SAM

**Use when:**
- Need CloudFormation integration
- Local testing required
- Infrastructure as Code focus

**Commands:**
```bash
sam build
sam deploy --guided  # First time
sam deploy           # Subsequent
sam local invoke -e test-event.json  # Local test
```

### Method 3: Plain AWS CLI Script

**Use when:**
- No additional tools available
- CI/CD pipeline integration
- Full control needed

**Commands:**
```bash
./deploy_lambda.sh --function-name service-name-dev --region us-east-1
```

### Lambda Function Naming Conventions

**CRITICAL:** Lambda function names must follow consistent patterns across environments to work with VeloFlow's service registry.

**Serverless Framework Naming:**
- Format: `{service}-{stage}-{functionName}`
- Example: `veloflow-pdf-to-json-dev-processor`
- Automatically generated by Serverless Framework

**Manual Naming:**
- Dev: `service-name-dev`
- QA: `service-name-qa`
- Prod: `service-name-prod`
- Example: `financial-processor-dev`

**Important Notes:**
- Keep function names consistent across all environments
- Update VeloFlow service registry after deployment with exact Lambda function names
- Mismatched names between registry and actual Lambda functions will cause invocation errors
- Use `scripts/register_service.py` in VeloFlow repository to update the registry

---

## Service Registration with VeloFlow

After deploying your service, register it with VeloFlow's orchestrator:

1. **Update Service Registry** (in VeloFlow repository):
   ```bash
   cd ~/git/VeloFlow
   python scripts/register_service.py \
     --service-id your-service-v1 \
     --lambda-dev your-service-dev \
     --lambda-qa your-service-qa \
     --lambda-prod your-service-prod \
     --description "Your service description"
   ```

2. **Verify Registration**:
   - Check `src/data/service_registry.json` in VeloFlow repository
   - Ensure Lambda function names match exactly across all environments
   - Test service invocation through VeloFlow workflows

3. **Common Registration Issues**:
   - **Cross-environment invocation errors**: Lambda name mismatch between dev/qa/prod
   - **Service not found**: Service ID doesn't match registry entry
   - **Permission errors**: Lambda execution role missing required permissions

**Reference:**
- VeloFlow Integration Guide: `~/git/VeloFlow/VELOFLOW_INTEGRATION_GUIDE.md`
- Service Registry: `~/git/VeloFlow/src/data/service_registry.json`
- Architecture Docs: `~/git/VeloFlow/docs/architecture/external-service-integration.md`

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Hardcoding Output Key
```python
# WRONG
output_key = f"jobs/{job_id}/output.xlsx"
```

**Fix:** Always use `event.get('output_key')` first

### ❌ Mistake 2: Not Emitting Progress
```python
# WRONG - No progress events
result = process_large_file()
```

**Fix:** Emit progress at key checkpoints

### ❌ Mistake 3: Forgetting to Write Output File
```python
# WRONG - Function returns but no file written
def process_file(input_path, output_path, config, emitter):
    result = do_processing(input_path)
    return {'success': True}  # output_path not written!
```

**Fix:** Always write to `output_path` before returning

### ❌ Mistake 4: Not Cleaning Up Temp Files
```python
# WRONG - Files left in /tmp
local_input_path.unlink()  # No error handling
```

**Fix:** Already handled in main handler with try/except

### ❌ Mistake 5: Incorrect Service ID Format
```python
# WRONG
SERVICE_ID = "MyService"  # CamelCase
SERVICE_ID = "my_service"  # underscores
```

**Fix:** Use lowercase-with-hyphens-v1 format

### ❌ Mistake 6: Missing Required Dependencies
```txt
# WRONG - forgot to add dependencies
boto3>=1.34.0
# ... missing openpyxl that code uses
```

**Fix:** Test locally first to catch import errors

### ❌ Mistake 7: Wrong ContentType for S3 Upload
The handler uses generic ContentType. Update if needed:
```python
s3_client.put_object(
    Bucket=bucket,
    Key=key,
    Body=f,
    ContentType='application/json'  # Update as needed
)
```

---

## Integration Checklist

Before marking service as complete, verify:

- [ ] Service name updated in all config files
- [ ] Service ID matches naming convention (lowercase-with-hyphens-v1)
- [ ] `process_file()` function completely replaced with actual logic
- [ ] Output file is written to `output_path`
- [ ] Progress events emitted at 3-5 key checkpoints
- [ ] Dependencies added to requirements.txt
- [ ] Environment variables added to .env.sample and configs
- [ ] Test event updated with appropriate test data
- [ ] Output file extension correct in fallback output_key
- [ ] IAM permissions sufficient for service needs
- [ ] Memory/timeout appropriate for processing time
- [ ] Function deployed successfully
- [ ] Test invocation succeeds
- [ ] Output file appears in S3
- [ ] CloudWatch logs show expected output
- [ ] Progress events visible (if testing with VeloFlow)
- [ ] Error handling tested (with invalid input)
- [ ] README.md updated with service-specific docs

---

## File Reference

### DO NOT MODIFY (Keep as-is):
- `service_event_emitter.py` - Ready to use
- Event validation logic (lines 70-91 in lambda_handler.py)
- S3 download/upload logic (lines 122-202 in lambda_handler.py)
- Error handling structure (lines 210-250 in lambda_handler.py)
- `.gitignore` - Comprehensive and correct

### MUST MODIFY (For every service):
- Service name in: serverless.yml, template.yaml, package.json, deploy_lambda.sh
- `SERVICE_ID` constant in lambda_handler.py
- `process_file()` function in lambda_handler.py
- Output file extension in fallback output_key
- requirements.txt dependencies
- Service description in configs and README

### SHOULD MODIFY (Based on needs):
- Memory/timeout settings
- Environment variables
- IAM permissions
- test-event.json
- Ephemeral storage size

---

## Support and Resources

**VeloFlow Documentation:**
- Integration Guide: `~/git/VeloFlow/VELOFLOW_INTEGRATION_GUIDE.md`
- Registration: `~/git/VeloFlow/scripts/register_service.py`

**Example Services:**
- PDF Processing: `~/git/service-pdf-to-xls-vision/`
- Financial Processing: `~/git/service-financial-processing/`

**Template Documentation:**
- Main README: `README.md` (comprehensive guide)
- Quick Guide: `TEMPLATE_GUIDE.md` (step-by-step)
- This file: `.claude/CLAUDE.md` (AI assistant instructions)

---

## Summary for Claude

When helping with this template:

1. **ALWAYS ask for service details first** (name, ID, input/output types, requirements)
2. **Update all config files** with the service name/ID consistently
3. **Focus on the `process_file()` function** - this is the main customization point
4. **Preserve VeloFlow integration** - don't break event handling or response format
5. **Use output_key from event** - never hardcode the output path format
6. **Add progress events** - minimum 3-5 checkpoints in processing
7. **Test thoroughly** - deploy, invoke, check logs and S3 output
8. **Update documentation** - README.md with service-specific details

The template is production-ready. Your job is to customize it for the specific service while maintaining all VeloFlow integration points.
