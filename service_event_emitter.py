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
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3


class ServiceEventEmitter:
    """Emits real-time progress events to VeloFlow EventBridge event bus."""

    def __init__(
        self,
        job_id: str,
        service_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        deployment_stage: Optional[str] = None
    ):
        """
        Initialize the event emitter.

        Args:
            job_id: VeloFlow job ID
            service_id: Unique identifier for this service (e.g., 'pdf-to-xls-vision-v1')
                       Defaults to 'unknown-service' if not provided
            stage_id: Optional workflow stage ID
            deployment_stage: Deployment stage like 'dev', 'qa', 'prod'
                            Defaults to STAGE environment variable or 'dev'
        """
        self.job_id = job_id
        self.service_id = service_id or 'unknown-service'
        self.stage_id = stage_id
        self.deployment_stage = deployment_stage or os.environ.get('STAGE', 'dev')
        self.events_client = boto3.client('events')
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME', f'veloflow-{self.deployment_stage}-event-bus')

    def emit_progress(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit a progress event.

        Args:
            message: Progress message to display to user
            metadata: Optional additional metadata
        """
        detail = {
            'job_id': self.job_id,
            'service_id': self.service_id,
            'status': 'in_progress',
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if self.stage_id:
            detail['stage_id'] = self.stage_id

        if metadata:
            detail['metadata'] = metadata

        self._emit_event('service.progress', detail)

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
            'job_id': self.job_id,
            'service_id': self.service_id,
            'status': 'success',
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if self.stage_id:
            detail['stage_id'] = self.stage_id

        if output_key:
            detail["output_key"] = output_key

        if metadata:
            detail['metadata'] = metadata

        self._emit_event('service.completed', detail)

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
            'job_id': self.job_id,
            'service_id': self.service_id,
            'status': 'error',
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if self.stage_id:
            detail['stage_id'] = self.stage_id

        if error_type:
            detail["error_type"] = error_type

        if metadata:
            detail['metadata'] = metadata

        self._emit_event('service.failed', detail)

    def _emit_event(self, event_type: str, detail: Dict[str, Any]) -> None:
        """
        Internal method to emit an event to EventBridge.

        Args:
            event_type: Event detail type (e.g., 'service.progress')
            detail: Event detail payload
        """
        try:
            self.events_client.put_events(
                Entries=[
                    {
                        'Source': 'veloflow.service',
                        'DetailType': event_type,
                        'Detail': json.dumps(detail, default=str),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            print(f"✓ Emitted event: {event_type} - {detail.get('message', '')}")
        except Exception as e:
            # Don't fail the service if event emission fails
            print(f"Warning: Failed to emit event: {e}")


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
