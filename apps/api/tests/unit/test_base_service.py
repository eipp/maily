"""
Unit tests for base service class.
"""
import pytest
import logging
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from apps.api.services.base_service import BaseService, ServiceMetrics


class TestServiceMetrics:
    """Tests for ServiceMetrics class."""

    def test_get_average_latency_empty(self):
        """Test average latency calculation with empty list."""
        metrics = ServiceMetrics()
        assert metrics.get_average_latency() == 0.0

    def test_get_average_latency(self):
        """Test average latency calculation."""
        metrics = ServiceMetrics(latency_ms=[10.0, 20.0, 30.0])
        assert metrics.get_average_latency() == 20.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = ServiceMetrics(
            requests_count=10,
            success_count=8,
            error_count=2,
            latency_ms=[10.0, 20.0, 30.0]
        )

        result = metrics.to_dict()
        assert result["requests_count"] == 10
        assert result["success_count"] == 8
        assert result["error_count"] == 2
        assert result["average_latency_ms"] == 20.0
        assert result["total_latency_ms"] == 60.0


class TestBaseService:
    """Tests for BaseService class."""

    def test_init(self):
        """Test service initialization."""
        mock_db = MagicMock()
        mock_settings = MagicMock()

        service = BaseService(db=mock_db, settings=mock_settings)

        assert service.db == mock_db
        assert service.settings == mock_settings
        assert isinstance(service.metrics, ServiceMetrics)

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test async initialization."""
        service = BaseService()
        # This should not raise any exceptions
        await service.initialize()

    def test_log_error(self):
        """Test error logging."""
        service = BaseService()
        error = ValueError("Test error")
        context = {"param": "value"}

        with patch.object(service.logger, "error") as mock_error:
            service.log_error(error, context)

            mock_error.assert_called_once()
            # Check that the error message and context were included
            args, kwargs = mock_error.call_args
            assert "Test error" in args[0]
            assert kwargs["extra"]["error_type"] == "ValueError"
            assert kwargs["extra"]["param"] == "value"

        assert service.metrics.error_count == 1

    def test_log_success(self):
        """Test success logging."""
        service = BaseService()
        operation = "test_operation"
        latency = 15.5

        with patch.object(service.logger, "info") as mock_info:
            service.log_success(operation, latency)

            mock_info.assert_called_once()
            # Check that the operation and latency were included
            args, kwargs = mock_info.call_args
            assert operation in args[0]
            assert kwargs["extra"]["operation"] == operation
            assert kwargs["extra"]["latency_ms"] == latency

        assert service.metrics.success_count == 1
        assert service.metrics.latency_ms == [latency]

    def test_get_metrics(self):
        """Test getting metrics."""
        service = BaseService()
        service.metrics.requests_count = 5
        service.metrics.success_count = 4
        service.metrics.error_count = 1
        service.metrics.latency_ms = [10.0, 20.0]

        metrics = service.get_metrics()

        assert metrics["requests_count"] == 5
        assert metrics["success_count"] == 4
        assert metrics["error_count"] == 1
        assert metrics["average_latency_ms"] == 15.0
        assert metrics["total_latency_ms"] == 30.0

    def test_reset_metrics(self):
        """Test resetting metrics."""
        service = BaseService()
        service.metrics.requests_count = 5
        service.metrics.success_count = 4
        service.metrics.error_count = 1
        service.metrics.latency_ms = [10.0, 20.0]

        service.reset_metrics()

        assert service.metrics.requests_count == 0
        assert service.metrics.success_count == 0
        assert service.metrics.error_count == 0
        assert service.metrics.latency_ms == []

    @pytest.mark.asyncio
    async def test_handle_common_exceptions_success(self):
        """Test exception handling decorator with successful execution."""
        service = BaseService()

        @BaseService.handle_common_exceptions
        async def test_func(self, param):
            return f"Success: {param}"

        result = await test_func(service, "test")
        assert result == "Success: test"

    @pytest.mark.asyncio
    async def test_handle_common_exceptions_http_exception(self):
        """Test exception handling decorator with HTTP exception."""
        service = BaseService()
        http_exception = HTTPException(status_code=404, detail="Not found")

        @BaseService.handle_common_exceptions
        async def test_func(self, param):
            raise http_exception

        with pytest.raises(HTTPException) as excinfo:
            await test_func(service, "test")

        assert excinfo.value == http_exception

    @pytest.mark.asyncio
    async def test_handle_common_exceptions_general_exception(self):
        """Test exception handling decorator with general exception."""
        service = BaseService()

        @BaseService.handle_common_exceptions
        async def test_func(self, param):
            raise ValueError("Test error")

        with patch.object(service, "log_error") as mock_log_error:
            with pytest.raises(HTTPException) as excinfo:
                await test_func(service, "test")

            assert excinfo.value.status_code == 500
            assert "Test error" in excinfo.value.detail
            mock_log_error.assert_called_once()
