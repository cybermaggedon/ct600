"""HMRC submission logic and async operations for ct600 module."""

import asyncio
import time
from typing import Optional

import aiohttp

from .govtalk import (
    GovTalkMessage, GovTalkSubmissionRequest, GovTalkSubmissionPoll, 
    GovTalkDeleteRequest, GovTalkSubmissionError, GovTalkSubmissionResponse,
    sr_Message
)
from .config import CT600Config
from .constants import SUBMISSION_TIMEOUT_SECONDS, OUTPUT_LINE_LENGTH
from .exceptions import SubmissionError, SubmissionTimeoutError


class SubmissionManager:
    """Manages HMRC submission process."""
    
    def __init__(self, config: CT600Config):
        """Initialize submission manager.
        
        Args:
            config: CT600 configuration object
        """
        self.config = config
    
    async def submit_request(self, request: GovTalkSubmissionRequest) -> GovTalkSubmissionResponse:
        """Submit a request to HMRC and handle polling.
        
        Args:
            request: The submission request to send
            
        Returns:
            The final submission response
            
        Raises:
            SubmissionError: If submission fails
            SubmissionTimeoutError: If polling times out
        """
        # Initial submission
        response = await self._send_request(request, self.config.submission_url)
        
        correlation_id = response.get("correlation-id")
        endpoint = response.get("response-endpoint")
        
        try:
            poll_interval = float(response.get("poll-interval"))
        except (TypeError, ValueError):
            poll_interval = None
        
        print(f"Correlation ID is {correlation_id}")
        
        # Poll until we get a final response
        timeout_time = time.time() + SUBMISSION_TIMEOUT_SECONDS
        
        while not isinstance(response, GovTalkSubmissionResponse):
            if time.time() > timeout_time:
                raise SubmissionTimeoutError(
                    "Timeout waiting for valid response",
                    correlation_id=correlation_id,
                    timeout_seconds=SUBMISSION_TIMEOUT_SECONDS
                )
            
            if poll_interval is None:
                raise SubmissionError(
                    "Should be polling, but have no poll information?",
                    correlation_id=correlation_id
                )
            
            await asyncio.sleep(poll_interval)
            
            # Create poll request
            poll_request = GovTalkSubmissionPoll(
                self.config.get_poll_params(correlation_id)
            )
            
            print("Poll...")
            response = await self._send_request(poll_request, endpoint)
            
            # Update polling parameters
            correlation_id = response.get("correlation-id")
            endpoint = response.get("response-endpoint")
            try:
                poll_interval = float(response.get("poll-interval"))
            except (TypeError, ValueError):
                poll_interval = None
        
        # Process successful response
        self._print_success_messages(response)
        
        # Clean up if we have a correlation ID
        if correlation_id:
            await self._cleanup_submission(correlation_id, endpoint)
        
        return response
    
    async def _send_request(self, request: GovTalkMessage, url: str) -> GovTalkMessage:
        """Send a single request to HMRC.
        
        Args:
            request: The request to send
            url: The URL to send to
            
        Returns:
            The response message
            
        Raises:
            SubmissionError: If request fails
        """
        async with aiohttp.ClientSession() as session:
            data = request.toxml()
            
            async with session.post(url, data=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(error_text)
                    raise SubmissionError(
                        f"Transaction failed: status={resp.status}",
                        status_code=resp.status
                    )
                
                response_data = await resp.text()
                
                message = GovTalkMessage.decode(response_data)
                
                if isinstance(message, GovTalkSubmissionError):
                    print(response_data)
                    error_text = message.get("error-text")
                    raise SubmissionError(error_text)
                
                return message
    
    def _print_success_messages(self, response: GovTalkSubmissionResponse) -> None:
        """Print success messages from response.
        
        Args:
            response: The successful submission response
        """
        success_response = response.get("success-response")
        if success_response is not None:
            for element in success_response.findall(".//" + sr_Message):
                print("- Message " + "-" * (OUTPUT_LINE_LENGTH - 10))
                print(element.text)
        
        print("-" * OUTPUT_LINE_LENGTH)
        print("Submission was successful.")
    
    async def _cleanup_submission(self, correlation_id: str, endpoint: str) -> None:
        """Clean up submission using delete request.
        
        Args:
            correlation_id: The correlation ID to delete
            endpoint: The endpoint to send delete request to
        """
        if not correlation_id:
            print("Completed.")
            return
        
        delete_request = GovTalkDeleteRequest(
            self.config.get_poll_params(correlation_id)
        )
        
        print("Delete request...")
        await self._send_request(delete_request, endpoint)
        print("Completed.")


def create_submission_request(config: CT600Config, utr: str, 
                            ir_envelope_tree) -> GovTalkSubmissionRequest:
    """Create a GovTalk submission request.
    
    Args:
        config: CT600 configuration
        utr: Unique Taxpayer Reference
        ir_envelope_tree: The IR envelope XML tree
        
    Returns:
        Configured submission request
    """
    request_params = config.get_request_params(utr, ir_envelope_tree.getroot())
    return GovTalkSubmissionRequest(request_params)


async def submit_to_hmrc(config: CT600Config, request: GovTalkSubmissionRequest) -> None:
    """Submit a request to HMRC with full error handling.
    
    Args:
        config: CT600 configuration
        request: The submission request
        
    Raises:
        SubmissionError: If submission fails
        SubmissionTimeoutError: If submission times out
    """
    # Add IRmark to request
    request.add_irmark()
    print(f"IRmark is {request.get_irmark()}")
    
    # Create submission manager and submit
    manager = SubmissionManager(config)
    await manager.submit_request(request)