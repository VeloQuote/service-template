"""Unit tests for VeloFlow Service Lambda Handler.

This is a template test file. Customize it for your specific service:
- Add tests for your process_file() function
- Add service-specific validation tests
- Add tests for custom configuration handling
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lambda_handler  # noqa: E402
from lambda_handler import lambda_handler as handler  # noqa: E402


def create_mock_path(path_str):
    """Create a mock Path object that doesn't touch filesystem.

    Note: /tmp is the standard temporary directory for AWS Lambda - using it in tests
    is safe and mirrors the actual Lambda environment.
    """
    from pathlib import Path as RealPath

    real_path = RealPath(path_str)

    mock_path = MagicMock()
    mock_path.name = real_path.name
    mock_path.__str__ = MagicMock(return_value=str(real_path))
    mock_path.__truediv__ = lambda self, other: create_mock_path(str(real_path / other))

    # Mock filesystem operations
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    mock_path.stat = MagicMock(return_value=mock_stat)
    mock_path.unlink = MagicMock()

    return mock_path


def path_constructor_mock(path_arg):
    """Mock for Path() constructor."""
    return create_mock_path(str(path_arg))


class TestEventValidation:
    """Test event validation logic."""

    def test_missing_invocation_type(self):
        """Test that missing invocation_type returns error."""
        event = {
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "key",
            "output_bucket": "output",
        }
        result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "invocation type" in result["error"].lower()

    def test_invalid_invocation_type(self):
        """Test that non-direct invocation type returns error."""
        event = {
            "invocation_type": "async",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "key",
            "output_bucket": "output",
        }
        result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "direct" in result["error"].lower()

    def test_missing_job_id(self):
        """Test that missing job_id returns error."""
        event = {
            "invocation_type": "direct",
            "input_bucket": "bucket",
            "input_key": "key",
            "output_bucket": "output",
        }
        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "job_id" in result["error"]

    def test_missing_input_bucket(self):
        """Test that missing input_bucket returns error."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_key": "key",
            "output_bucket": "output",
        }
        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "input_bucket" in result["error"]

    def test_missing_input_key(self):
        """Test that missing input_key returns error."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "output_bucket": "output",
        }
        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "input_key" in result["error"]

    def test_missing_output_bucket(self):
        """Test that missing output_bucket returns error."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "key",
        }
        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValidationError"
        assert "output_bucket" in result["error"]


class TestOutputKeyHandling:
    """Test output_key handling for multi-stage workflows."""

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_uses_provided_output_key(self, mock_emitter, mock_process, mock_s3):
        """Test that provided output_key is used (multi-stage workflow)."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "input-bucket",
            "input_key": "input.xlsx",
            "output_bucket": "output-bucket",
            "output_key": "jobs/test-123/stage-2/custom-output.xlsx",
        }

        # Mock file operations
        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}

        # Mock emitter
        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "success"
        assert result["output_key"] == "jobs/test-123/stage-2/custom-output.xlsx"

        # Verify upload was called with the provided output_key
        assert mock_s3.upload_file.called
        upload_call = mock_s3.upload_file.call_args
        assert upload_call[0][2] == "jobs/test-123/stage-2/custom-output.xlsx"

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_fallback_output_key_legacy_workflow(
        self, mock_emitter, mock_process, mock_s3
    ):
        """Test fallback output_key for legacy single-stage workflows."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-456",
            "input_bucket": "input-bucket",
            "input_key": "input.xlsx",
            "output_bucket": "output-bucket",
            # No output_key provided
        }

        # Mock file operations
        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}

        # Mock emitter
        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "success"
        # Default fallback uses generic extension - customize this based on your service
        assert "jobs/test-456" in result["output_key"]


class TestOptionalParameters:
    """Test handling of optional parameters."""

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_default_customer_tier(self, mock_emitter, mock_process, mock_s3):
        """Test that customer_tier defaults to 'standard'."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "key",
            "output_bucket": "output",
        }

        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}

        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "success"
        assert result["metadata"]["customer_tier"] == "standard"

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_reference_date_included_in_metadata(
        self, mock_emitter, mock_process, mock_s3
    ):
        """Test that reference_date is included in metadata when provided."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "key",
            "output_bucket": "output",
            "reference_date": "2025-01-15",
        }

        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}

        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "success"
        assert result["metadata"]["reference_date"] == "2025-01-15"


class TestErrorHandling:
    """Test error handling for different exception types."""

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_file_not_found_error(self, mock_emitter, mock_s3):
        """Test FileNotFoundError handling."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "missing.xlsx",
            "output_bucket": "output",
        }

        mock_s3.download_file.side_effect = FileNotFoundError("File not found in S3")
        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "FileNotFoundError"
        assert "not found" in result["error"].lower()
        assert mock_emitter_instance.emit_error.called

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_value_error_handling(self, mock_emitter, mock_process, mock_s3):
        """Test ValueError handling from process_file."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "invalid.xlsx",
            "output_bucket": "output",
        }

        mock_s3.download_file = MagicMock()
        mock_process.side_effect = ValueError("Invalid file format")

        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "ValueError"
        assert "Invalid value" in result["error"]
        assert mock_emitter_instance.emit_error.called

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_general_exception_handling(self, mock_emitter, mock_process, mock_s3):
        """Test generic Exception handling."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-123",
            "input_bucket": "bucket",
            "input_key": "file.xlsx",
            "output_bucket": "output",
        }

        mock_s3.download_file = MagicMock()
        mock_process.side_effect = RuntimeError("Unexpected processing error")

        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "error"
        assert result["error_type"] == "RuntimeError"
        assert "Unexpected processing error" in result["error"]
        assert mock_emitter_instance.emit_error.called


class TestSuccessfulExecution:
    """Test successful execution flow."""

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_complete_success_flow(self, mock_emitter, mock_process, mock_s3):
        """Test complete successful execution with all metadata."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-success-123",
            "input_bucket": "input-bucket",
            "input_key": "uploads/sample.xlsx",
            "output_bucket": "output-bucket",
            "output_key": "jobs/test-success-123/output.xlsx",
            "reference_date": "2025-01-15",
            "customer_tier": "premium",
            "stage_config": {
                "stage_id": "processing",
                "custom_param": "value",
            },
        }

        # Mock S3 operations
        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()

        # Mock process_file return
        mock_process.return_value = {
            "success": True,
            "metadata": {
                "records_processed": 42,
                "custom_metric": "test",
            },
        }

        # Mock emitter
        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        # Verify success response
        assert result["status"] == "success"
        assert result["output_bucket"] == "output-bucket"
        assert result["output_key"] == "jobs/test-success-123/output.xlsx"

        # Verify metadata
        assert "processing_time_ms" in result["metadata"]
        assert "input_file_size_bytes" in result["metadata"]
        assert "output_file_size_bytes" in result["metadata"]
        assert result["metadata"]["customer_tier"] == "premium"
        assert result["metadata"]["reference_date"] == "2025-01-15"
        assert result["metadata"]["records_processed"] == 42

        # Verify progress events were emitted
        assert mock_emitter_instance.emit_progress.call_count >= 4
        assert mock_emitter_instance.emit_success.called

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_config_passed_to_process_file(self, mock_emitter, mock_process, mock_s3):
        """Test that stage_config is properly passed to process_file."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-config-123",
            "input_bucket": "bucket",
            "input_key": "file.xlsx",
            "output_bucket": "output",
            "stage_config": {
                "template_name": "custom_template",
                "custom_param": "value",
            },
        }

        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}

        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            result = handler(event, None)

        assert result["status"] == "success"

        # Verify process_file was called with correct config
        call_args = mock_process.call_args
        config_arg = call_args[1]["config"]
        assert config_arg["template_name"] == "custom_template"
        assert config_arg["custom_param"] == "value"


class TestServiceEventEmitter:
    """Test ServiceEventEmitter integration."""

    @patch("lambda_handler.s3_client")
    @patch("lambda_handler.process_file")
    @patch("lambda_handler.ServiceEventEmitter")
    def test_emitter_initialized_with_correct_params(
        self, mock_emitter, mock_process, mock_s3
    ):
        """Test that ServiceEventEmitter is initialized with correct parameters."""
        event = {
            "invocation_type": "direct",
            "job_id": "test-emitter-123",
            "input_bucket": "bucket",
            "input_key": "file.xlsx",
            "output_bucket": "output",
            "stage_config": {"stage_id": "custom-stage-id"},
        }

        mock_s3.download_file = MagicMock()
        mock_s3.upload_file = MagicMock()
        mock_process.return_value = {"success": True, "metadata": {}}
        mock_emitter_instance = MagicMock()
        mock_emitter.return_value = mock_emitter_instance

        # Mock Path to avoid filesystem operations
        with patch("lambda_handler.Path", side_effect=path_constructor_mock), patch(
            "lambda_handler.TMP_DIR", create_mock_path("/tmp")  # nosec B108
        ):
            handler(event, None)

        # Verify emitter was initialized correctly
        mock_emitter.assert_called_once_with(
            job_id="test-emitter-123",
            service_id=lambda_handler.SERVICE_ID,
            stage_id="custom-stage-id",
        )


# =============================================================================
# TODO: Add service-specific tests below
# =============================================================================
#
# class TestProcessFile:
#     """Tests for your service-specific process_file() function."""
#
#     @patch("lambda_handler.process_file")
#     def test_your_specific_processing(self, mock_process):
#         """Test your service's processing logic."""
#         pass
#
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=lambda_handler", "--cov-report=term-missing"])
