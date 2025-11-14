# VeloFlow Service Template - Setup Guide

## What's Included

This template provides everything you need to create a VeloFlow-compatible Lambda service:

### Core Files

1. **`lambda_handler.py`** (10KB)
   - Complete VeloFlow-compatible Lambda handler
   - Handles VeloFlow event format with all required fields
   - Proper `output_key` handling for multi-stage workflows
   - Error handling with proper error types
   - S3 download/upload logic
   - Clear TODOs for customization
   - Example `process_file()` function to replace with your logic

2. **`service_event_emitter.py`** (6.7KB)
   - Ready-to-use EventBridge integration
   - Methods: `emit_progress()`, `emit_success()`, `emit_error()`
   - Automatic error handling (won't break your service)
   - No modification needed

### Deployment Options (Choose One)

3. **`serverless.yml`** (4.5KB) - Serverless Framework
   - Simple, developer-friendly configuration
   - Stage management (dev/staging/prod)
   - NPM scripts for easy deployment
   - Recommended for most services

4. **`template.yaml`** (4.5KB) - AWS SAM
   - Native CloudFormation support
   - Good for infrastructure-heavy services
   - Local testing capabilities

5. **`deploy_lambda.sh`** (7.2KB) - Plain AWS CLI
   - No additional tools required
   - Full control over deployment
   - Good for CI/CD pipelines

### Configuration Files

6. **`requirements.txt`** (541B)
   - Python dependencies template
   - Includes boto3 (AWS SDK)
   - Comments showing common dependencies to add

7. **`.env.sample`**
   - Environment variables template
   - Copy to `.env` for local development
   - Contains all standard VeloFlow variables

8. **`.gitignore`**
   - Comprehensive ignore rules
   - Covers Python, AWS, deployment artifacts

9. **`package.json`** (1.1KB)
   - NPM scripts for Serverless Framework
   - Convenient deploy/logs/info commands

10. **`test-event.json`** (360B)
    - Sample VeloFlow event for testing
    - Update with your test data

### Documentation

11. **`README.md`** (14KB)
    - Complete setup and customization guide
    - VeloFlow integration details
    - Deployment instructions for all methods
    - Troubleshooting guide
    - Best practices

---

## Quick Start (5 Minutes)

### Step 1: Copy Template
```bash
cp -r ~/git/service-template ~/git/service-YOUR-NAME
cd ~/git/service-YOUR-NAME
```

### Step 2: Find and Replace
Replace these strings throughout the project:

| Find | Replace With | Files |
|------|--------------|-------|
| `service-template` | `service-YOUR-NAME` | serverless.yml, template.yaml, package.json |
| `your-service-v1` | `YOUR-NAME-v1` | lambda_handler.py, .env.sample |
| `TODO: Replace this with your actual file processing logic` | Your actual code | lambda_handler.py |

### Step 3: Implement Your Logic

Edit `lambda_handler.py` and replace the `process_file()` function (around line 240):

```python
def process_file(
    input_path: Path,
    output_path: Path,
    config: Dict[str, Any],
    emitter: ServiceEventEmitter
) -> Dict[str, Any]:
    """
    YOUR SERVICE LOGIC HERE
    """
    # 1. Read input file
    # 2. Process data
    # 3. Write output file
    # 4. Return metadata
```

### Step 4: Add Dependencies

Edit `requirements.txt` and add your dependencies:
```txt
boto3>=1.34.0
# Add your dependencies:
openpyxl>=3.1.0
pillow>=10.0.0
```

### Step 5: Deploy

**Option A: Serverless (Recommended)**
```bash
npm install
npm run deploy:dev
```

**Option B: AWS SAM**
```bash
sam build
sam deploy --guided
```

**Option C: AWS CLI Script**
```bash
./deploy_lambda.sh --function-name YOUR-SERVICE-dev
```

### Step 6: Test

```bash
# Update test event with your data
vim test-event.json

# Test the function
aws lambda invoke \
  --function-name YOUR-SERVICE-dev \
  --payload file://test-event.json \
  response.json

# Check response
cat response.json | jq
```

### Step 7: Register with VeloFlow

```bash
cd ~/git/VeloFlow
python3 scripts/register_service.py \
  --service-id "YOUR-NAME-v1" \
  --service-name "Your Service Name" \
  --service-type "custom" \
  --lambda-name "YOUR-SERVICE-dev" \
  --stage dev
```

---

## Key Features Already Implemented

### ✅ VeloFlow Event Processing
- Validates `invocation_type` is "direct"
- Extracts all required fields: `job_id`, `input_bucket`, `input_key`, `output_bucket`
- Handles optional fields: `output_key`, `reference_date`, `customer_tier`, `stage_config`
- Proper fallback for legacy workflows (when `output_key` not provided)

### ✅ Real-time Progress Updates
- ServiceEventEmitter properly initialized
- Progress events at key checkpoints
- Success event with output location
- Error events with proper error types
- Non-blocking (won't fail your service if EventBridge has issues)

### ✅ S3 Operations
- Downloads input file from S3
- Uploads output file to S3
- Proper error handling for S3 operations
- File size tracking
- Cleanup of temporary files

### ✅ Error Handling
- All exceptions caught and handled
- Standardized error responses
- Error events emitted to VeloFlow
- Detailed error context in responses
- Traceback logging

### ✅ IAM Permissions
- S3 read permissions for input/processing buckets
- S3 write permissions for processing/output buckets
- EventBridge PutEvents permission
- CloudWatch Logs permissions

### ✅ Production Configuration
- 3008 MB memory (adjustable)
- 900s timeout (15 minutes)
- 2048 MB ephemeral storage
- CloudWatch alarms for errors and duration
- Log retention policy (30 days)
- Proper tagging

---

## What You Need to Customize

### Must Customize

1. **Service Name** (in all config files)
2. **Service ID** (in lambda_handler.py)
3. **`process_file()` function** (your actual logic)
4. **Dependencies** (in requirements.txt)

### Optional Customization

5. **Memory/Timeout** (if different from 3008MB/900s)
6. **Environment Variables** (if you need custom ones)
7. **IAM Permissions** (if you need additional AWS services)
8. **File Extension** (default is .xlsx, change if needed)
9. **Progress Messages** (customize to match your workflow)

---

## Integration Checklist

Before going live, verify:

- [ ] Service name updated in all files
- [ ] Service ID matches what you'll register in VeloFlow
- [ ] `process_file()` function replaced with actual logic
- [ ] Dependencies added to requirements.txt
- [ ] Environment variables configured
- [ ] Function deployed successfully
- [ ] Test event works correctly
- [ ] S3 permissions verified (can read input, write output)
- [ ] EventBridge permissions verified (progress events appear)
- [ ] CloudWatch logs accessible
- [ ] Error handling tested
- [ ] Function registered in VeloFlow
- [ ] End-to-end test through VeloFlow UI

---

## Common Customizations

### Add Database Access

**In serverless.yml:**
```yaml
environment:
  DB_TABLE_NAME: my-table

iamRoleStatements:
  - Effect: Allow
    Action:
      - dynamodb:GetItem
      - dynamodb:PutItem
    Resource:
      - arn:aws:dynamodb:*:*:table/my-table
```

### Add API Key

**In serverless.yml:**
```yaml
environment:
  API_KEY: ${env:API_KEY}
```

**In .env:**
```
API_KEY=your-key-here
```

### Change Output Format

**In lambda_handler.py:**
```python
# Change from .xlsx to .json
output_key = event.get('output_key')
if not output_key:
    output_key = f"jobs/{job_id}/output.json"  # Change extension
```

### Add Validation

**In lambda_handler.py:**
```python
# After extracting parameters, add validation
if not input_key.endswith('.pdf'):
    return {
        'status': 'error',
        'error': 'Input must be a PDF file',
        'error_type': 'ValidationError'
    }
```

---

## File-by-File Guide

### lambda_handler.py (Main Handler)

**Lines to Customize:**
- Line 52-53: Update `SERVICE_ID` and `SERVICE_VERSION`
- Line 98: Update output file extension if needed
- Line 245-280: Replace `process_file()` with your logic

**What to Keep:**
- Event validation (lines 70-91)
- S3 download logic (lines 122-130)
- S3 upload logic (lines 192-202)
- Error handling (lines 210-250)
- Response format (lines 260-273)

### serverless.yml (Serverless Config)

**Lines to Customize:**
- Line 2: Update service name
- Line 20-23: Add your environment variables
- Line 78: Update function description

**What to Keep:**
- Provider configuration (lines 3-10)
- Memory/timeout settings (lines 12-13)
- IAM permissions (lines 28-59)

### requirements.txt (Dependencies)

**Add your dependencies after boto3**

Common additions:
```txt
# PDF processing
pypdf2>=3.0.0

# Excel processing
openpyxl>=3.1.0
pandas>=2.0.0

# AI services
anthropic>=0.18.0

# Image processing
pillow>=10.0.0
```

---

## Next Steps After Deployment

1. **Monitor CloudWatch Logs**
   ```bash
   npm run logs:dev
   ```

2. **Test with Real Data**
   - Upload a file through VeloFlow UI
   - Monitor progress messages
   - Verify output file

3. **Set Up Alarms**
   - Already configured in template
   - Add SNS notifications if needed

4. **Document Your Service**
   - Update README.md with service-specific info
   - Add examples of input/output
   - Document any special configuration

5. **Add Tests**
   - Use the `tests/` directory
   - Add unit tests for your logic
   - Add integration tests

---

## Support

If you have questions:

1. Review the main README.md
2. Check VeloFlow integration guide: `~/git/VeloFlow/VELOFLOW_INTEGRATION_GUIDE.md`
3. Look at example services:
   - `~/git/service-pdf-to-xls-vision`
   - `~/git/service-financial-processing`

---

**Template Version**: 1.0.0
**Last Updated**: 2025-11-14
