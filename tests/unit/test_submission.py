"""Unit tests for submission module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import ClientSession

from ct600.submission import (
    SubmissionManager, create_submission_request, submit_to_hmrc
)
from ct600.config import CT600Config
from ct600.govtalk import (
    GovTalkSubmissionRequest, GovTalkSubmissionPoll, GovTalkDeleteRequest,
    GovTalkSubmissionError, GovTalkSubmissionResponse, GovTalkSubmissionAcknowledgement
)
from ct600.exceptions import SubmissionError, SubmissionTimeoutError


class TestSubmissionManager:
    """Test SubmissionManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        return CT600Config(config_data)
    
    @pytest.fixture
    def submission_manager(self, mock_config):
        """Create SubmissionManager instance."""
        return SubmissionManager(mock_config)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock submission request."""
        request = Mock(spec=GovTalkSubmissionRequest)
        request.toxml.return_value = "<xml>test</xml>"
        return request
    
    @pytest.fixture
    def mock_successful_response(self):
        """Create mock successful response."""
        response = Mock(spec=GovTalkSubmissionResponse)
        response.get.side_effect = lambda key: {
            "correlation-id": "test-correlation-123",
            "response-endpoint": "https://example.com/poll",
            "poll-interval": "5.0"
        }.get(key)
        
        # Mock success response element
        mock_success_response = Mock()
        mock_element = Mock()
        mock_element.text = "Submission processed successfully"
        mock_success_response.findall.return_value = [mock_element]
        response.get.return_value = mock_success_response
        
        return response
    
    @pytest.fixture
    def mock_acknowledgement_response(self):
        """Create mock acknowledgement response."""
        response = Mock(spec=GovTalkSubmissionAcknowledgement)
        response.get.side_effect = lambda key: {
            "correlation-id": "test-correlation-123",
            "response-endpoint": "https://example.com/poll",
            "poll-interval": "5.0"
        }.get(key)
        return response
    
    @pytest.mark.asyncio
    async def test_send_request_success(self, submission_manager, mock_request):
        """Test successful request sending."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<response>success</response>")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('ct600.submission.GovTalkMessage.decode') as mock_decode:
                mock_message = Mock()
                mock_decode.return_value = mock_message
                
                result = await submission_manager._send_request(
                    mock_request, "https://example.com/api"
                )
                
                assert result is mock_message
                mock_session.post.assert_called_once_with(
                    "https://example.com/api", data="<xml>test</xml>"
                )
    
    @pytest.mark.asyncio
    async def test_send_request_http_error(self, submission_manager, mock_request):
        """Test request sending with HTTP error."""
        mock_response = Mock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(SubmissionError) as exc_info:
                await submission_manager._send_request(
                    mock_request, "https://example.com/api"
                )
            
            assert "Transaction failed: status=500" in str(exc_info.value)
            assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_send_request_govtalk_error(self, submission_manager, mock_request):
        """Test request sending with GovTalk error response."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<error>Invalid request</error>")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        mock_error_message = Mock(spec=GovTalkSubmissionError)
        mock_error_message.get.return_value = "Invalid request format"
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('ct600.submission.GovTalkMessage.decode', return_value=mock_error_message):
                with pytest.raises(SubmissionError) as exc_info:
                    await submission_manager._send_request(
                        mock_request, "https://example.com/api"
                    )
                
                assert "Invalid request format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_submit_request_immediate_success(self, submission_manager, mock_request, 
                                                   mock_successful_response):
        """Test submission that succeeds immediately."""
        # Mock _send_request to return final response immediately
        submission_manager._send_request = AsyncMock(return_value=mock_successful_response)
        submission_manager._cleanup_submission = AsyncMock()
        
        with patch('builtins.print'):  # Suppress print output
            result = await submission_manager.submit_request(mock_request)
        
        assert result is mock_successful_response
        submission_manager._send_request.assert_called_once()
        submission_manager._cleanup_submission.assert_called_once_with(
            "test-correlation-123", "https://example.com/poll"
        )
    
    @pytest.mark.asyncio
    async def test_submit_request_with_polling(self, submission_manager, mock_request,
                                              mock_acknowledgement_response, mock_successful_response):
        """Test submission that requires polling."""
        # First call returns acknowledgement, second returns success
        submission_manager._send_request = AsyncMock(side_effect=[
            mock_acknowledgement_response,
            mock_successful_response
        ])
        submission_manager._cleanup_submission = AsyncMock()
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with patch('builtins.print'):  # Suppress print output
                result = await submission_manager.submit_request(mock_request)
        
        assert result is mock_successful_response
        assert submission_manager._send_request.call_count == 2
        
        # Check that poll request was created
        second_call_args = submission_manager._send_request.call_args_list[1]
        poll_request = second_call_args[0][0]
        assert isinstance(poll_request, GovTalkSubmissionPoll)
    
    @pytest.mark.asyncio
    async def test_submit_request_timeout(self, submission_manager, mock_request,
                                         mock_acknowledgement_response):
        """Test submission timeout."""
        # Always return acknowledgement (never final response)
        submission_manager._send_request = AsyncMock(return_value=mock_acknowledgement_response)
        
        with patch('time.time', side_effect=[0, 200]):  # Simulate timeout
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with patch('builtins.print'):  # Suppress print output
                    with pytest.raises(SubmissionTimeoutError) as exc_info:
                        await submission_manager.submit_request(mock_request)
        
        assert "Timeout waiting for valid response" in str(exc_info.value)
        assert exc_info.value.correlation_id == "test-correlation-123"
        assert exc_info.value.timeout_seconds == 120
    
    @pytest.mark.asyncio
    async def test_submit_request_no_poll_interval(self, submission_manager, mock_request):
        """Test submission with missing poll interval."""
        mock_response = Mock()
        mock_response.get.side_effect = lambda key: {
            "correlation-id": "test-correlation-123",
            "response-endpoint": "https://example.com/poll",
            "poll-interval": None  # Missing poll interval
        }.get(key)
        
        submission_manager._send_request = AsyncMock(return_value=mock_response)
        
        with patch('time.time', return_value=0):
            with patch('builtins.print'):  # Suppress print output
                with pytest.raises(SubmissionError) as exc_info:
                    await submission_manager.submit_request(mock_request)
        
        assert "Should be polling, but have no poll information?" in str(exc_info.value)
        assert exc_info.value.correlation_id == "test-correlation-123"
    
    def test_print_success_messages(self, submission_manager, mock_successful_response):
        """Test printing success messages."""
        with patch('builtins.print') as mock_print:
            submission_manager._print_success_messages(mock_successful_response)
            
            # Should print message separator and content
            mock_print.assert_any_call("- Message " + "-" * 66)
            mock_print.assert_any_call("Submission processed successfully")
            mock_print.assert_any_call("-" * 76)
            mock_print.assert_any_call("Submission was successful.")
    
    @pytest.mark.asyncio
    async def test_cleanup_submission(self, submission_manager):
        """Test submission cleanup."""
        submission_manager._send_request = AsyncMock()
        
        with patch('builtins.print') as mock_print:
            await submission_manager._cleanup_submission(
                "test-correlation-123", "https://example.com/poll"
            )
        
        # Should create delete request
        call_args = submission_manager._send_request.call_args
        delete_request = call_args[0][0]
        assert isinstance(delete_request, GovTalkDeleteRequest)
        
        mock_print.assert_any_call("Delete request...")
        mock_print.assert_any_call("Completed.")
    
    @pytest.mark.asyncio
    async def test_cleanup_submission_no_correlation_id(self, submission_manager):
        """Test cleanup with no correlation ID."""
        with patch('builtins.print') as mock_print:
            await submission_manager._cleanup_submission("", "https://example.com/poll")
        
        # Should just print completed
        mock_print.assert_called_once_with("Completed.")


class TestCreateSubmissionRequest:
    """Test create_submission_request function."""
    
    def test_create_submission_request(self):
        """Test creating submission request."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        config = CT600Config(config_data)
        
        mock_tree = Mock()
        mock_root = Mock()
        mock_tree.getroot.return_value = mock_root
        
        with patch('ct600.submission.GovTalkSubmissionRequest') as mock_request_class:
            mock_request = Mock()
            mock_request_class.return_value = mock_request
            
            result = create_submission_request(config, "1234567890", mock_tree)
            
            assert result is mock_request
            
            # Check that request was created with correct parameters
            call_args = mock_request_class.call_args[0][0]
            assert call_args["username"] == "test_user"
            assert call_args["password"] == "test_pass"
            assert call_args["tax-reference"] == "1234567890"
            assert call_args["ir-envelope"] is mock_root


class TestSubmitToHMRC:
    """Test submit_to_hmrc function."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        return CT600Config(config_data)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock submission request."""
        request = Mock(spec=GovTalkSubmissionRequest)
        request.add_irmark.return_value = None
        request.get_irmark.return_value = "mock-irmark-123"
        return request
    
    @pytest.mark.asyncio
    async def test_submit_to_hmrc_success(self, mock_config, mock_request):
        """Test successful HMRC submission."""
        mock_manager = Mock()
        mock_manager.submit_request = AsyncMock()
        
        with patch('ct600.submission.SubmissionManager', return_value=mock_manager):
            with patch('builtins.print') as mock_print:
                await submit_to_hmrc(mock_config, mock_request)
        
        # Should add IRmark and print it
        mock_request.add_irmark.assert_called_once()
        mock_request.get_irmark.assert_called_once()
        mock_print.assert_called_with("IRmark is mock-irmark-123")
        
        # Should create manager and submit
        mock_manager.submit_request.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_submit_to_hmrc_submission_error(self, mock_config, mock_request):
        """Test HMRC submission with error."""
        mock_manager = Mock()
        mock_manager.submit_request = AsyncMock(side_effect=SubmissionError("Test error"))
        
        with patch('ct600.submission.SubmissionManager', return_value=mock_manager):
            with patch('builtins.print'):
                with pytest.raises(SubmissionError) as exc_info:
                    await submit_to_hmrc(mock_config, mock_request)
        
        assert "Test error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_submit_to_hmrc_timeout_error(self, mock_config, mock_request):
        """Test HMRC submission with timeout."""
        mock_manager = Mock()
        mock_manager.submit_request = AsyncMock(
            side_effect=SubmissionTimeoutError("Timeout occurred")
        )
        
        with patch('ct600.submission.SubmissionManager', return_value=mock_manager):
            with patch('builtins.print'):
                with pytest.raises(SubmissionTimeoutError) as exc_info:
                    await submit_to_hmrc(mock_config, mock_request)
        
        assert "Timeout occurred" in str(exc_info.value)


class TestSubmissionIntegration:
    """Integration tests for submission functionality."""
    
    @pytest.mark.asyncio
    async def test_full_submission_workflow(self):
        """Test complete submission workflow."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        config = CT600Config(config_data)
        
        # Mock HTTP responses
        initial_response = Mock()
        initial_response.status = 200
        initial_response.text = AsyncMock(return_value="<ack>acknowledged</ack>")
        
        final_response = Mock()
        final_response.status = 200
        final_response.text = AsyncMock(return_value="<success>completed</success>")
        
        # Mock GovTalk messages
        mock_ack = Mock(spec=GovTalkSubmissionAcknowledgement)
        mock_ack.get.side_effect = lambda key: {
            "correlation-id": "test-123",
            "response-endpoint": "https://example.com/poll",
            "poll-interval": "1.0"
        }.get(key)
        
        mock_success = Mock(spec=GovTalkSubmissionResponse)
        mock_success.get.side_effect = lambda key: {
            "correlation-id": "test-123",
            "success-response": Mock()
        }.get(key) if key == "success-response" else "test-123"
        
        mock_success_response = Mock()
        mock_success_response.findall.return_value = []
        mock_success.get.return_value = mock_success_response
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.post.side_effect = [
            mock_session.post.return_value.__aenter__.return_value,
            mock_session.post.return_value.__aenter__.return_value,
            mock_session.post.return_value.__aenter__.return_value
        ]
        mock_session.post.return_value.__aenter__.return_value = initial_response
        
        # Set up the sequence of responses
        responses = [mock_ack, mock_success, Mock()]  # Last one for delete
        
        mock_request = Mock(spec=GovTalkSubmissionRequest)
        mock_request.add_irmark.return_value = None
        mock_request.get_irmark.return_value = "test-irmark"
        mock_request.toxml.return_value = "<xml>test</xml>"
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('ct600.submission.GovTalkMessage.decode', side_effect=responses):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    with patch('builtins.print'):
                        manager = SubmissionManager(config)
                        
                        # This should work without raising exceptions
                        await manager.submit_request(mock_request)
        
        # Verify the workflow
        assert mock_session.post.call_count >= 2  # Initial + poll (+ delete)
    
    def test_config_parameter_inheritance(self):
        """Test that configuration parameters are properly inherited."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": False,
            "vendor-id": "vendor_123",
            "url": "https://production.hmrc.gov.uk/api",
            "class": "CUSTOM-CLASS"
        }
        config = CT600Config(config_data)
        manager = SubmissionManager(config)
        
        # Test that manager maintains reference to config
        assert manager.config is config
        assert manager.config.is_test_gateway is False
        assert manager.config.submission_url == "https://production.hmrc.gov.uk/api"
        
        # Test poll params generation
        poll_params = manager.config.get_poll_params("test-correlation")
        assert poll_params["class"] == "CUSTOM-CLASS"
        assert poll_params["gateway-test"] is False
        assert poll_params["correlation-id"] == "test-correlation"