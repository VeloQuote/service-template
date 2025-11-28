#!/usr/bin/env python3
"""Update VeloFlow service registry with current Lambda function.

This script registers/updates a service in the VeloFlow service registry
after deployment. This allows VeloFlow to discover and invoke the correct
Lambda function for service jobs.

Usage:
    python scripts/update_service_registry.py --stage dev
    python scripts/update_service_registry.py --stage qa
    python scripts/update_service_registry.py --stage prod

Configuration:
    Update the configuration constants below with your service-specific values.
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add VeloFlow to path for ServiceRegistryHelper
veloflow_path = os.path.expanduser('~/git/VeloFlow')
if os.path.exists(veloflow_path):
    sys.path.insert(0, veloflow_path)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 is not installed. Install with: pip install boto3")
    sys.exit(1)

# Try to import ServiceRegistryHelper from VeloFlow
try:
    from src.utils.service_registry_helper import ServiceRegistryHelper
    USE_HELPER = True
except ImportError:
    print("⚠️  Warning: ServiceRegistryHelper not found (VeloFlow not in ~/git/VeloFlow)")
    print("   Falling back to direct DynamoDB operations")
    USE_HELPER = False

# ============================================================================
# SERVICE CONFIGURATION - UPDATE THESE FOR YOUR SERVICE
# ============================================================================

# Service Name - Used to construct Lambda function name
# This should match the service name in serverless.yml (without veloflow- prefix)
SERVICE_NAME = "service-template"

# Service Type - Category of service for discovery
# Examples: 'pdf_processor', 'financial_processor', 'formatter', 'analyzer', etc.
SERVICE_TYPE = "template"

# Service Display Name - Human-readable name
SERVICE_DISPLAY_NAME = "VeloFlow Service Template"

# Service Priority - Lower number = higher priority (default: 10)
# Use 1-5 for critical services, 10 for standard, 20+ for low priority
PRIORITY = 10

# Service Capabilities - What your service can do
CAPABILITIES = {
    "description": "Template service for creating new VeloFlow services",
    "supported_formats": ["any"],  # e.g., ["xlsx", "pdf", "json"]
    "max_file_size_mb": 50,
    "output_format": "any",  # e.g., "xlsx", "json", "pdf"
    # Add service-specific capabilities:
    # "validation": True,
    # "multi_period": True,
    # "ai_powered": True,
}

# Service Constraints - Resource limits and quotas
CONSTRAINTS = {
    "max_concurrency": 10,
    "rate_limit_per_minute": 60,
    "timeout_seconds": 900,  # Should match Lambda timeout
    "memory_mb": 3008,       # Should match Lambda memory
}

# Parameter Definitions - User-configurable parameters for this service
# These appear in the VeloFlow UI when configuring workflow stages
PARAMETER_DEFINITIONS = [
    # Example parameter:
    # {
    #     'name': 'processing_date',
    #     'type': 'date',
    #     'required': False,
    #     'description': 'Reference date for data processing',
    #     'placeholder': '2025-01-15'
    # },
    # {
    #     'name': 'output_format',
    #     'type': 'select',
    #     'required': False,
    #     'description': 'Output file format',
    #     'options': ['xlsx', 'csv', 'json'],
    #     'default': 'xlsx'
    # },
    # {
    #     'name': 'enable_validation',
    #     'type': 'boolean',
    #     'required': False,
    #     'description': 'Enable data validation',
    #     'default': True
    # }
]

# Service Metadata - Additional information
METADATA = {
    "version": "1.0.0",
    "description": "Template service for creating new VeloFlow Lambda services",
    "use_cases": [
        "Service template customization",
        "VeloFlow integration examples",
    ],
    # Add environment-specific metadata if needed
}

# ============================================================================
# END CONFIGURATION
# ============================================================================


def register_service_with_helper(stage: str) -> bool:
    """Register service using ServiceRegistryHelper (preferred method).

    Args:
        stage: Deployment stage (dev, qa, staging, or prod)

    Returns:
        True if successful, False otherwise
    """
    # Construct Lambda details
    lambda_name = f"veloflow-{stage}-{SERVICE_NAME}"
    lambda_arn = f"arn:aws:lambda:us-east-1:346871995105:function:{lambda_name}"
    service_id = f"{SERVICE_NAME}-{stage}-v1"

    print(f"Registering service using ServiceRegistryHelper...")
    print(f"  Service ID: {service_id}")
    print(f"  Lambda: {lambda_name}")

    try:
        helper = ServiceRegistryHelper(region='us-east-1', stage=stage)

        # Build service data
        service_data = {
            'service_id': service_id,
            'service_type': SERVICE_TYPE,
            'service_name': SERVICE_DISPLAY_NAME,
            'lambda_arn': lambda_arn,
            'lambda_name': lambda_name,
            'enabled': True,
            'priority': PRIORITY,
            'capabilities': CAPABILITIES.copy(),
            'constraints': CONSTRAINTS.copy(),
            'metadata': {
                **METADATA,
                'environment': stage,
                'registered_at': datetime.utcnow().isoformat() + 'Z',
            }
        }

        # Add parameter definitions if configured
        if PARAMETER_DEFINITIONS:
            service_data['parameter_definitions'] = PARAMETER_DEFINITIONS.copy()

        # Register service
        success = helper.register_service(service_data)

        if success:
            print(f"\n✅ Successfully registered service")
            print(f"   Service ID: {service_id}")
            print(f"   Service Type: {SERVICE_TYPE}")
            print(f"   Priority: {PRIORITY}")
            if PARAMETER_DEFINITIONS:
                print(f"\n   Parameters:")
                for param in PARAMETER_DEFINITIONS:
                    required_str = "Required" if param.get('required') else "Optional"
                    print(f"     - {param['name']} ({param['type']}, {required_str})")

        return success

    except Exception as e:
        print(f"❌ Error using ServiceRegistryHelper: {e}")
        return False


def register_service_direct(stage: str) -> bool:
    """Register service using direct DynamoDB access (fallback method).

    Args:
        stage: Deployment stage (dev, qa, staging, or prod)

    Returns:
        True if successful, False otherwise
    """
    # Construct Lambda details
    lambda_name = f"veloflow-{stage}-{SERVICE_NAME}"
    lambda_arn = f"arn:aws:lambda:us-east-1:346871995105:function:{lambda_name}"
    service_id = f"{SERVICE_NAME}-{stage}-v1"
    table_name = f"veloflow-{stage}-service-registry"

    print(f"Registering service using direct DynamoDB access...")
    print(f"  Service ID: {service_id}")
    print(f"  Lambda: {lambda_name}")
    print(f"  Table: {table_name}")

    try:
        # Initialize AWS clients
        lambda_client = boto3.client("lambda")
        dynamodb = boto3.resource("dynamodb")

        # Get Lambda function details (validates it exists)
        try:
            response = lambda_client.get_function(FunctionName=lambda_name)
            function_arn = response["Configuration"]["FunctionArn"]
            print(f"✅ Found Lambda function: {lambda_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"❌ Error: Lambda function '{lambda_name}' not found")
                print("   Make sure the function is deployed to this stage")
                return False
            else:
                print(f"❌ Error getting Lambda function: {e}")
                return False

        # Get table reference
        table = dynamodb.Table(table_name)

        # Build service registration
        service_data = {
            'service_id': service_id,
            'service_type': SERVICE_TYPE,
            'service_name': SERVICE_DISPLAY_NAME,
            'lambda_arn': function_arn,
            'lambda_name': lambda_name,
            'enabled': True,
            'priority': PRIORITY,
            'capabilities': CAPABILITIES.copy(),
            'constraints': CONSTRAINTS.copy(),
            'health': {
                'status': 'healthy',
                'last_check': datetime.utcnow().isoformat() + 'Z',
                'error_rate': 0.0,
                'avg_duration_ms': 0,
                'p99_duration_ms': 0,
                'success_count_24h': 0,
                'failure_count_24h': 0,
            },
            'metadata': {
                **METADATA,
                'environment': stage,
                'registered_at': datetime.utcnow().isoformat() + 'Z',
            }
        }

        # Add parameter definitions if configured
        if PARAMETER_DEFINITIONS:
            service_data['parameter_definitions'] = PARAMETER_DEFINITIONS.copy()

        # Register in DynamoDB
        table.put_item(Item=service_data)

        print(f"\n✅ Successfully registered service")
        print(f"   Service ID: {service_id}")
        print(f"   Service Type: {SERVICE_TYPE}")
        print(f"   Priority: {PRIORITY}")
        print(f"   Status: active")

        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"❌ Error: DynamoDB table '{table_name}' not found")
            print("   The VeloFlow service registry may not be set up for this stage")
            print("")
            print("   NOTE: Service registry is OPTIONAL. Your service will work")
            print("   without it, but VeloFlow won't be able to auto-discover it.")
            return False
        else:
            print(f"❌ Error updating service registry: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_registration(stage: str) -> bool:
    """Verify service registration exists and is correct.

    Args:
        stage: Deployment stage (dev, qa, staging, or prod)

    Returns:
        True if verification successful, False otherwise
    """
    service_id = f"{SERVICE_NAME}-{stage}-v1"

    print(f"\n🔍 Verifying service registration...")

    if USE_HELPER:
        try:
            helper = ServiceRegistryHelper(region='us-east-1', stage=stage)
            service = helper.get_service(service_id)

            if service:
                print(f"✅ Service registry entry verified")
                print(f"   Service ID: {service.get('service_id')}")
                print(f"   Lambda Name: {service.get('lambda_name')}")
                print(f"   Enabled: {service.get('enabled')}")
                print(f"   Priority: {service.get('priority')}")
                return True
            else:
                print(f"❌ Service registry entry not found")
                return False
        except Exception as e:
            print(f"⚠️  Warning: Could not verify registry entry: {e}")
            return False
    else:
        # Direct DynamoDB verification
        try:
            dynamodb = boto3.resource("dynamodb")
            table_name = f"veloflow-{stage}-service-registry"
            table = dynamodb.Table(table_name)

            response = table.get_item(Key={"service_id": service_id})

            if "Item" in response:
                item = response["Item"]
                print(f"✅ Service registry entry verified")
                print(f"   Service ID: {item.get('service_id')}")
                print(f"   Lambda Name: {item.get('lambda_name')}")
                print(f"   Enabled: {item.get('enabled')}")
                print(f"   Priority: {item.get('priority')}")
                return True
            else:
                print(f"❌ Service registry entry not found")
                return False
        except Exception as e:
            print(f"⚠️  Warning: Could not verify registry entry: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Register/update VeloFlow service in service registry"
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=["dev", "qa", "staging", "prod"],
        help="Deployment stage (dev, qa, staging, or prod)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify registry entry, do not update",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("VeloFlow Service Registry Update")
    print("=" * 70)
    print()

    if args.verify_only:
        success = verify_registration(args.stage)
    else:
        # Try ServiceRegistryHelper first, fall back to direct access
        if USE_HELPER:
            success = register_service_with_helper(args.stage)
        else:
            success = register_service_direct(args.stage)

        if success:
            verify_registration(args.stage)

    print()
    print("=" * 70)

    if success:
        print("✅ Service registry operation completed successfully")
        sys.exit(0)
    else:
        print("❌ Service registry operation failed")
        print("")
        print("NOTE: Service registry is OPTIONAL for development.")
        print("Your service will still work without it!")
        sys.exit(1)


if __name__ == "__main__":
    main()
