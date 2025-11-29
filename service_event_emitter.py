"""Service Event Emitter for VeloFlow real-time progress updates.

This module provides a class for emitting real-time progress, success, and error
events to the VeloFlow EventBridge event bus. These events are automatically
forwarded to WebSocket clients for real-time UI updates.

Usage:
    from service_event_emitter import ServiceEventEmitter

    emitter = ServiceEventEmitter(
        job_id='a2df38da-edd6-4c75-b90f-4114f3cf1edf',
        service_id='pdf-to-xls-vision-v1',
        stage_id='vision-conversion'
    )

    # Emit progress
    emitter.emit_progress('Processing page 1 of 5...')

    # Emit success
    emitter.emit_success(
        'Conversion completed successfully',
        output_key='jobs/abc/output.xlsx'
    )

    # Emit error
    emitter.emit_error(
        'Failed to process page 3',
        error_type='TableExtractionError'
    )
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError


class ServiceEventEmitter:
    """Emits real-time progress events to VeloFlow EventBridge event bus."""

    def __init__(self, job_id: str, service_id: str, stage_id: Optional[str] = None):
        """
        Initialize the event emitter.

        Args:
            job_id: VeloFlow job ID
            service_id: Unique identifier for this service (e.g., 'pdf-to-xls-vision-v1')
            stage_id: Optional workflow stage ID
        """
        self.job_id = job_id
        self.service_id = service_id
        self.stage_id = stage_id
        self.event_bus_name = os.environ.get("EVENT_BUS_NAME")

        # Initialize EventBridge client
        self.events_client = boto3.client("events")

    def emit_progress(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit a progress event.

        Args:
            message: Progress message to display to user
            metadata: Optional additional metadata
        """
        self._emit_event(
            event_type="service.progress",
            detail={
                "job_id": self.job_id,
                "service_id": self.service_id,
                "stage_id": self.stage_id,
                "status": "in_progress",
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    def emit_success(
        self,
        message: str,
        output_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit a success event.

        Args:
            message: Success message to display to user
            output_key: Optional S3 key of the output file
            metadata: Optional additional metadata
        """
        detail = {
            "job_id": self.job_id,
            "service_id": self.service_id,
            "stage_id": self.stage_id,
            "status": "success",
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if output_key:
            detail["output_key"] = output_key

        self._emit_event(event_type="service.completed", detail=detail)

    def emit_error(
        self,
        message: str,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Emit an error event.

        Args:
            message: Error message to display to user
            error_type: Optional error type/classification
            metadata: Optional additional error context
        """
        detail = {
            "job_id": self.job_id,
            "service_id": self.service_id,
            "stage_id": self.stage_id,
            "status": "error",
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if error_type:
            detail["error_type"] = error_type

        self._emit_event(event_type="service.failed", detail=detail)

    def _emit_event(self, event_type: str, detail: Dict[str, Any]) -> None:
        """
        Internal method to emit an event to EventBridge.

        Args:
            event_type: Event detail type (e.g., 'service.progress')
            detail: Event detail payload
        """
        # Skip if no event bus configured
        if not self.event_bus_name:
            print(
                f"Warning: EVENT_BUS_NAME not set, skipping event emission: {event_type}"
            )
            return

        try:
            # Prepare event entry
            event_entry = {
                "Source": "veloflow.service",
                "DetailType": event_type,
                "Detail": json.dumps(detail),
                "EventBusName": self.event_bus_name,
            }

            # Publish to EventBridge
            response = self.events_client.put_events(Entries=[event_entry])

            # Check for failures
            if response.get("FailedEntryCount", 0) > 0:
                failed = response.get("Entries", [{}])[0]
                error_code = failed.get("ErrorCode", "Unknown")
                error_msg = failed.get("ErrorMessage", "Unknown error")
                print(f"Warning: Failed to emit event: {error_code} - {error_msg}")
            else:
                print(f"✓ Emitted event: {event_type} - {detail.get('message', '')}")

        except ClientError as e:
            # Don't fail the Lambda if event emission fails
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            print(
                f"Warning: Failed to emit event to EventBridge: {error_code} - {error_msg}"
            )

        except Exception as e:
            # Catch any other exceptions to prevent breaking the service
            print(f"Warning: Unexpected error emitting event: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Set mock environment variable for testing
    os.environ["EVENT_BUS_NAME"] = "veloflow-dev-event-bus"

    # Create emitter
    emitter = ServiceEventEmitter(
        job_id="test-job-123",
        service_id="pdf-to-xls-vision-v1",
        stage_id="vision-conversion",
    )

    # Test emissions
    emitter.emit_progress("Starting conversion...")
    emitter.emit_progress("Processing page 1 of 3...", metadata={"page": 1, "total": 3})
    emitter.emit_success(
        "Conversion completed successfully",
        output_key="jobs/test-job-123/output.xlsx",
        metadata={"pages": 3, "tables": 5},
    )
