import unittest
from unittest.mock import MagicMock, patch
import json
from agentos_sdk.client import AgentOSClient

class TestAgentOSClient(unittest.TestCase):
    def setUp(self):
        self.client = AgentOSClient(
            api_url="http://test.api",
            api_key="test-key",
            agent_id="test-agent",
            agent_name="Test Agent",
            platform="test-platform"
        )
        # Mock the session
        self.client.session = MagicMock()
        self.client.session.post.return_value.status_code = 202
        self.client.session.post.return_value.json.return_value = {"accepted": 1}

    def test_trace_invocation(self):
        input_data = {"query": "hello"}
        
        with self.client.trace_invocation(input_data) as recorder:
            with recorder.create_span("step1", "system") as span:
                span.set_io("input", "output")
        
        # Verify post was called
        self.client.session.post.assert_called_once()
        
        # Verify payload
        args, kwargs = self.client.session.post.call_args
        url = args[0]
        payload = kwargs["json"]
        
        self.assertEqual(url, "http://test.api/v1/telemetry/events")
        self.assertIn("events", payload)
        self.assertEqual(len(payload["events"]), 2) # Root span + step1 span
        
        event = payload["events"][0]
        self.assertEqual(event["platform"], "test-platform")
        self.assertEqual(event["agent"]["name"], "Test Agent")
        self.assertIn("execution", event)
        self.assertIn("traceId", event["execution"])

if __name__ == "__main__":
    unittest.main()
