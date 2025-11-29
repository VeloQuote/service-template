"""VeloFlow Service Lambda Handler Template

This is a template for creating VeloFlow-compatible Lambda functions.
Replace the placeholder logic with your actual service implementation.

Event format:
{
  "invocation_type": "direct",
  "job_id": "a2df38da-edd6-4c75-b90f-4114f3cf1edf",
  "input_bucket": "veloflow-dev-input",
  "input_key": "uploads/user123/document.pdf",
  "output_bucket": "veloflow-dev-output",
  "output_key": "jobs/a2df38da/stage-1/output.xlsx",  # Optional
  "reference_date": "2025-01-15",
  "customer_tier": "standard",
  "stage_config": {
    "custom_param1": "value1",
    "custom_param2": "value2"
  }
}

Response format:
{
  "status": "success",
  "output_bucket": "veloflow-dev-output",
  "output_key": "jobs/a2df38da/output.xlsx",
  "metadata": {
    "processing_time_ms": 1234,
    "custom_metric": "value"
  }
}
"""

import json
import os
import time
import traceback
from pathlib import Path
from typing import Any, Dict

import boto3

from service_event_emitter import ServiceEventEmitter

# Initialize S3 client
s3_client = boto3.client("s3")

# Lambda tmp directory (hardcoded /tmp is standard for AWS Lambda)
TMP_DIR = Path("/tmp")  # nosec B108

# TODO: Update these constants for your service
SERVICE_ID = os.environ.get("SERVICE_ID", "your-service-v1")
SERVICE_VERSION = os.environ.get("SERVICE_VERSION", "1.0.0")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    VeloFlow-compatible Lambda handler.

    TODO: Customize this handler for your specific service logic.

    Args:
        event: VeloFlow event containing job_id, input/output buckets, and config
        context: Lambda context object

    Returns:
        Dict with status, output location, and metadata
    """
    start_time = time.time()

    try:
        # 1. Validate event format
        print(f"Received event: {json.dumps(event)}")

        if event.get("invocation_type") != "direct":
            return {
                "status": "error",
                "error": 'Invalid invocation type. Expected "direct"',
                "error_type": "ValidationError",
            }

        # 2. Extract required parameters
        try:
            job_id = event["job_id"]
            input_bucket = event["input_bucket"]
            input_key = event["input_key"]
            output_bucket = event["output_bucket"]
        except KeyError as e:
            return {
                "status": "error",
                "error": f"Missing required field: {str(e)}",
                "error_type": "ValidationError",
            }

        # 3. Extract optional parameters
        reference_date = event.get("reference_date")
        customer_tier = event.get("customer_tier", "standard")
        stage_config = event.get("stage_config", {})

        # IMPORTANT: Use provided output_key for multi-stage workflow support
        output_key = event.get("output_key")
        if not output_key:
            # Fallback for legacy single-stage workflows
            # TODO: Update file extension as needed (.xlsx, .json, .pdf, etc.)
            output_key = f"jobs/{job_id}/output.xlsx"

        # TODO: Extract any custom parameters from stage_config
        # custom_param = stage_config.get('custom_param', 'default_value')

        # 4. Initialize progress emitter
        emitter = ServiceEventEmitter(
            job_id=job_id, service_id=SERVICE_ID, stage_id=stage_config.get("stage_id")
        )

        # 5. Emit starting progress
        emitter.emit_progress("Starting processing...")

        print(f"Processing job {job_id}")
        print(f"Input: s3://{input_bucket}/{input_key}")
        print(f"Output: s3://{output_bucket}/{output_key}")
        print(f"Customer tier: {customer_tier}")

        # 6. Download input file from S3
        emitter.emit_progress("Downloading input file from S3...")

        input_filename = Path(input_key).name
        local_input_path = TMP_DIR / f"input_{job_id}_{input_filename}"

        print(f"Downloading s3://{input_bucket}/{input_key} to {local_input_path}")
        s3_client.download_file(input_bucket, input_key, str(local_input_path))

        file_size_bytes = local_input_path.stat().st_size
        print(f"Downloaded {file_size_bytes:,} bytes")

        # 7. Process the file
        # TODO: Replace this with your actual processing logic
        emitter.emit_progress("Processing file...")

        print("Starting file processing...")
        processing_start = time.time()

        # TODO: Call your processing function here
        local_output_path = TMP_DIR / f"output_{job_id}.xlsx"
        result = process_file(
            input_path=local_input_path,
            output_path=local_output_path,
            config=stage_config,
            emitter=emitter,
        )

        processing_time_ms = int((time.time() - processing_start) * 1000)
        print(f"Processing completed in {processing_time_ms}ms")

        # 8. Upload output file to S3
        emitter.emit_progress("Uploading output to S3...")

        print(f"Uploading {local_output_path} to s3://{output_bucket}/{output_key}")
        s3_client.upload_file(str(local_output_path), output_bucket, output_key)

        output_file_size = local_output_path.stat().st_size
        print(f"Uploaded {output_file_size:,} bytes")

        # 9. Clean up temporary files
        try:
            local_input_path.unlink()
            local_output_path.unlink()
            print("Cleaned up temporary files")
        except Exception as e:
            print(f"Warning: Failed to clean up temp files: {e}")

        # 10. Calculate total processing time
        total_time_ms = int((time.time() - start_time) * 1000)

        # 11. Build metadata
        metadata = {
            "processing_time_ms": total_time_ms,
            "input_file_size_bytes": file_size_bytes,
            "output_file_size_bytes": output_file_size,
            "customer_tier": customer_tier,
            "service_version": SERVICE_VERSION,
            # TODO: Add your custom metadata here
            **result.get("metadata", {}),
        }

        if reference_date:
            metadata["reference_date"] = reference_date

        # 12. Emit success event
        emitter.emit_success(
            "Processing completed successfully",
            output_key=output_key,
            metadata=metadata,
        )

        # 13. Return success response
        response = {
            "status": "success",
            "output_bucket": output_bucket,
            "output_key": output_key,
            "metadata": metadata,
        }

        print(f"Success! Total processing time: {total_time_ms}ms")
        print(f"Response: {json.dumps(response)}")

        return response

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        print(f"ERROR: {error_msg}")
        if "emitter" in locals():
            emitter.emit_error(error_msg, error_type="FileNotFoundError")
        return {
            "status": "error",
            "error": error_msg,
            "error_type": "FileNotFoundError",
            "metadata": {
                "job_id": event.get("job_id"),
                "input_key": event.get("input_key"),
            },
        }

    except ValueError as e:
        error_msg = f"Invalid value: {str(e)}"
        print(f"ERROR: {error_msg}")
        if "emitter" in locals():
            emitter.emit_error(error_msg, error_type="ValueError")
        return {
            "status": "error",
            "error": error_msg,
            "error_type": "ValueError",
            "metadata": {"job_id": event.get("job_id")},
        }

    except Exception as e:
        # Processing error
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        print(f"Traceback:\n{error_trace}")

        if "emitter" in locals():
            emitter.emit_error(error_msg, error_type=type(e).__name__)

        return {
            "status": "error",
            "error": error_msg,
            "error_type": type(e).__name__,
            "metadata": {
                "job_id": event.get("job_id"),
                "input_key": event.get("input_key"),
                "processing_time_ms": int((time.time() - start_time) * 1000),
            },
        }


def process_file(
    input_path: Path,
    output_path: Path,
    config: Dict[str, Any],
    emitter: ServiceEventEmitter,
) -> Dict[str, Any]:
    """
    TODO: Replace this with your actual file processing logic.

    This is a placeholder function that demonstrates the expected structure.

    Args:
        input_path: Path to input file
        output_path: Path to save output file
        config: Stage configuration from VeloFlow
        emitter: ServiceEventEmitter for real-time progress updates

    Returns:
        Dict containing processing results and metadata
    """
    # Example: Emit progress at key checkpoints
    emitter.emit_progress("Analyzing input file...")

    # TODO: Implement your processing logic here
    # Example steps:
    # 1. Parse input file
    # 2. Process data
    # 3. Generate output
    # 4. Write output file

    # Simulate processing for template
    import time

    time.sleep(2)  # Remove this in your implementation

    # Create a simple output file (replace with actual output)
    with open(output_path, "wb") as f:
        f.write(b"TODO: Replace with actual output")

    emitter.emit_progress("Processing complete")

    # Return metadata about processing
    return {
        "success": True,
        "metadata": {
            "records_processed": 0,  # TODO: Add actual metrics
            "custom_metric": "value",
        },
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "invocation_type": "direct",
        "job_id": "test-job-123",
        "input_bucket": "your-test-bucket",
        "input_key": "test/sample.pdf",
        "output_bucket": "your-test-bucket",
        "customer_tier": "standard",
        "stage_config": {},
    }

    # Run handler
    result = lambda_handler(test_event, None)
    print(f"\nResult: {json.dumps(result, indent=2)}")
