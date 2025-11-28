# Scripts Directory

This directory is reserved for service-specific utility scripts.

## Service Registration

**IMPORTANT:** Service registration is managed by VeloFlow, not by individual services.

### How Service Registration Works

1. **Service declares metadata** in `veloflow.json` at the root of the repo
2. **VeloFlow reads the metadata** and registers the service in its registry
3. **Service has no direct access** to VeloFlow's DynamoDB registry

### To Register Your Service

After deploying your Lambda function, use VeloFlow's registration tool:

```bash
cd ~/git/VeloFlow
python3 scripts/services/register_service.py <service-repo-path> --stage dev
```

Example:
```bash
cd ~/git/VeloFlow
python3 scripts/services/register_service.py ~/git/my-pdf-service --stage dev
```

This will:
1. Read `veloflow.json` from your service repo
2. Verify the Lambda function exists
3. Register the service in VeloFlow's service registry
4. Configure health monitoring

### Service Metadata (veloflow.json)

Your service metadata is defined in `veloflow.json` at the root of your repo.

Key sections:
- **service**: Name, description, type
- **lambda**: Runtime, memory, timeout configuration
- **capabilities**: What your service can do
- **parameters**: User-configurable parameters (shown in UI)
- **constraints**: Resource limits

See `veloflow.json` for the complete schema and examples.

## Custom Scripts

Add your service-specific scripts here:

- Data migration scripts
- Testing utilities
- Maintenance scripts
- One-off processing scripts

**Examples:**
```
scripts/
├── migrate_data.py
├── generate_test_data.py
├── cleanup_s3.py
└── README.md (this file)
```
