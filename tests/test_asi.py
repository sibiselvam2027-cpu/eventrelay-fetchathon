import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from eventrelay.asi import ASIError, extract_intent


def response(value):
    return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(value)}}]}).encode())


class ASITests(unittest.TestCase):
    def test_live_parser_keeps_key_out_of_model_input(self):
        data = {"action": "report", "category": "audio", "location": "Stage A",
                "summary": "Microphone is silent", "priority": "normal"}
        with patch.dict(os.environ, {"ASI1_API_KEY": "private-test-key"}), \
             patch("eventrelay.asi.urlopen", return_value=response(data)) as call:
            result = extract_intent("The mic at Stage A is silent", {"last_issue": None})
        self.assertEqual(result["category"], "audio")
        request = call.call_args.args[0]
        self.assertNotIn("private-test-key", request.data.decode())
        self.assertEqual(request.get_header("Authorization"), "Bearer private-test-key")

    def test_ambiguous_water_is_returned_for_clarification(self):
        data = {"action": "report", "category": "unknown", "location": "Stage",
                "summary": "Water issue", "priority": "normal", "missing_fields": ["category"],
                "clarification": "Do you mean drinking water, a spill, or a leak?"}
        with patch.dict(os.environ, {"ASI1_API_KEY": "test-key"}), \
             patch("eventrelay.asi.urlopen", return_value=response(data)) as call:
            result = extract_intent("Water at the stage")
        self.assertEqual(result["category"], "unknown")
        self.assertIsNotNone(result["clarification"])
        self.assertIn("do not guess", json.loads(call.call_args.args[0].data)["messages"][0]["content"])

    def test_honors_injected_hosted_api_base_url(self):
        data = {"action": "status", "category": "unknown", "priority": "normal"}
        with patch.dict(os.environ, {"ASI1_API_KEY": "hosted-quota-key", "ASI1_BASE_URL": "https://hosted.example/v1/"}), \
             patch("eventrelay.asi.urlopen", return_value=response(data)) as call:
            extract_intent("Show the current status")
        self.assertEqual(call.call_args.args[0].full_url, "https://hosted.example/v1/chat/completions")
        self.assertEqual(call.call_args.args[0].get_header("Authorization"), "Bearer hosted-quota-key")

    def test_refuses_insecure_api_base_url(self):
        with patch.dict(os.environ, {"ASI1_API_KEY": "test-key", "ASI1_BASE_URL": "http://untrusted.example/v1"}), \
             patch("eventrelay.asi.urlopen") as call:
            with self.assertRaises(ASIError):
                extract_intent("Show the current status")
        call.assert_not_called()

    def test_missing_key_has_no_silent_fixture(self):
        with patch.dict(os.environ, {}, clear=True), patch("eventrelay.asi.urlopen") as call:
            with self.assertRaises(ASIError):
                extract_intent("The microphone is silent")
            call.assert_not_called()

    def test_unsupported_category_is_rejected(self):
        with patch.dict(os.environ, {"ASI1_API_KEY": "test-key"}), \
             patch("eventrelay.asi.urlopen", return_value=response({"action": "report", "category": "send_money"})):
            with self.assertRaises(ASIError):
                extract_intent("hello")

    def test_malformed_action_is_safely_rejected(self):
        with patch.dict(os.environ, {"ASI1_API_KEY": "test-key"}), \
             patch("eventrelay.asi.urlopen", return_value=response({"action": ["report"]})):
            with self.assertRaises(ASIError):
                extract_intent("hello")

    def test_upstream_auth_error_is_sanitized(self):
        error = HTTPError("https://api.asi1.ai", 401, "private-upstream-text", {}, None)
        with patch.dict(os.environ, {"ASI1_API_KEY": "private-test-key"}), \
             patch("eventrelay.asi.urlopen", side_effect=error):
            with self.assertRaises(ASIError) as caught:
                extract_intent("hello")
        self.assertNotIn("private-test-key", str(caught.exception))
        self.assertNotIn("private-upstream-text", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
