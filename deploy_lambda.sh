#!/bin/bash
# Deploy VeloFlow Service Lambda Function
#
# Usage:
#   ./deploy_lambda.sh --function-name my-service --region us-east-1
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - Python 3.11+ installed
#   - pip installed
#
# TODO: Update default FUNCTION_NAME for your service

set -e

# Default values - TODO: Customize these for your service
FUNCTION_NAME="veloflow-service-template"
REGION="us-east-1"
RUNTIME="python3.11"
MEMORY="3008"
TIMEOUT="900"
EPHEMERAL_STORAGE="2048"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --function-name)
      FUNCTION_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --memory)
      MEMORY="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --function-name NAME    Lambda function name (default: veloflow-service-template)"
      echo "  --region REGION         AWS region (default: us-east-1)"
      echo "  --memory MB             Memory in MB (default: 3008)"
      echo "  --timeout SECONDS       Timeout in seconds (default: 900)"
      echo "  -h, --help              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "=========================================="
echo "VeloFlow Service - Lambda Deployment"
echo "=========================================="
echo ""
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Runtime: $RUNTIME"
echo "Memory: ${MEMORY}MB"
echo "Timeout: ${TIMEOUT}s"
echo "Ephemeral storage: ${EPHEMERAL_STORAGE}MB"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "Step 1: Creating Lambda layer with dependencies..."
echo "=================================================="

# Clean previous builds
rm -rf lambda-layer
rm -f dependencies.zip

# Create layer directory
mkdir -p lambda-layer/python

# Install dependencies
echo "Installing dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt -t lambda-layer/python/ --quiet
    echo "✓ Dependencies installed"
else
    echo "WARNING: requirements.txt not found, skipping dependencies"
fi

# Create layer zip
echo "Creating layer zip file..."
cd lambda-layer
zip -r ../dependencies.zip python/ > /dev/null
cd ..

LAYER_SIZE=$(du -h dependencies.zip | cut -f1)
echo "✓ Layer created: dependencies.zip ($LAYER_SIZE)"
echo ""

echo "Step 2: Publishing Lambda layer..."
echo "==================================="

LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name ${FUNCTION_NAME}-dependencies \
    --zip-file fileb://dependencies.zip \
    --compatible-runtimes $RUNTIME \
    --region $REGION \
    --query 'Version' \
    --output text)

echo "✓ Layer published: version $LAYER_VERSION"
echo ""

# Get layer ARN
LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name ${FUNCTION_NAME}-dependencies \
    --region $REGION \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)

echo "Layer ARN: $LAYER_ARN"
echo ""

echo "Step 3: Packaging function code..."
echo "==================================="

# Clean previous package
rm -f function.zip

# Create function zip
echo "Creating function zip..."
zip -r function.zip lambda_handler.py service_event_emitter.py > /dev/null

# TODO: Add any additional files or directories your service needs
# Example: zip -r function.zip lambda_handler.py service_event_emitter.py my_module/ > /dev/null

FUNCTION_SIZE=$(du -h function.zip | cut -f1)
echo "✓ Function packaged: function.zip ($FUNCTION_SIZE)"
echo ""

echo "Step 4: Checking if function exists..."
echo "======================================="

if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &> /dev/null; then
    echo "Function exists. Updating..."

    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://function.zip \
        --region $REGION \
        --query 'FunctionArn' \
        --output text > /dev/null

    echo "✓ Function code updated"

    # Update function configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers $LAYER_ARN \
        --memory-size $MEMORY \
        --timeout $TIMEOUT \
        --ephemeral-storage Size=$EPHEMERAL_STORAGE \
        --region $REGION \
        --query 'FunctionArn' \
        --output text > /dev/null

    echo "✓ Function configuration updated"

else
    echo "Function does not exist. Creating new function..."
    echo ""
    echo "NOTE: You need to provide an execution role ARN."
    echo "If you don't have one, create it in IAM with:"
    echo "  - AWSLambdaBasicExecutionRole"
    echo "  - S3 read/write permissions for veloflow-*-input and veloflow-*-output buckets"
    echo "  - EventBridge PutEvents permission for veloflow-*-event-bus"
    echo ""
    read -p "Enter execution role ARN: " ROLE_ARN

    if [ -z "$ROLE_ARN" ]; then
        echo "ERROR: Role ARN is required"
        exit 1
    fi

    # Create function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler lambda_handler.lambda_handler \
        --zip-file fileb://function.zip \
        --layers $LAYER_ARN \
        --memory-size $MEMORY \
        --timeout $TIMEOUT \
        --ephemeral-storage Size=$EPHEMERAL_STORAGE \
        --region $REGION \
        --query 'FunctionArn' \
        --output text > /dev/null

    echo "✓ Function created"
fi

echo ""

echo "Step 5: Setting environment variables..."
echo "========================================="

# TODO: Update these environment variables for your service
ENV_VARS="Variables={"
ENV_VARS="${ENV_VARS}SERVICE_ID=your-service-v1,"
ENV_VARS="${ENV_VARS}SERVICE_VERSION=1.0.0,"
ENV_VARS="${ENV_VARS}EVENT_BUS_NAME=veloflow-dev-event-bus"

# Add API keys if needed
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
fi

# TODO: Add any other environment variables your service needs
# ENV_VARS="${ENV_VARS},CUSTOM_VAR=${CUSTOM_VAR}"

ENV_VARS="${ENV_VARS}}"

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment "$ENV_VARS" \
    --region $REGION \
    --query 'FunctionArn' \
    --output text > /dev/null

echo "✓ Environment variables set"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Layer ARN: $LAYER_ARN"
echo ""
echo "Next steps:"
echo "1. Verify environment variables in Lambda console"
echo "2. Test the function with test-event.json"
echo "3. Register with VeloFlow"
echo ""
echo "Test command:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --payload file://test-event.json response.json --region $REGION"
echo ""
