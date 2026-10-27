import io
import json
import os
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from eventrelay.asi import ASIError, extract_intent, _sdk_completion


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

    def test_explicit_escalation_intent_preserves_reference_or_leaves_it_unlinked(self):
        for issue_id in (None, "ER-1234ABCD"):
            with self.subTest(issue_id=issue_id), \
                 patch.dict(os.environ, {"ASI1_API_KEY": "test-key"}, clear=True), \
                 patch("eventrelay.asi.urlopen", return_value=response({
                     "action": "escalate", "issue_id": issue_id, "note": "Crew has not responded."})):
                result = extract_intent("Please escalate this issue.")
            self.assertEqual("escalate", result["action"])
            self.assertEqual(issue_id, result["issue_id"])
            self.assertEqual("Crew has not responded.", result["note"])

    def test_honors_injected_hosted_api_base_url(self):
        data = {"action": "status", "category": "unknown", "priority": "normal"}
        with patch.dict(os.environ, {"ASI1_API_KEY": "hosted-quota-key", "ASI1_BASE_URL": "https://hosted.example/v1/"}), \
             patch("eventrelay.asi._sdk_completion", return_value=json.dumps(data)) as call:
            extract_intent("Show the current status")
        self.assertEqual(call.call_args.args[2], "https://hosted.example/v1")
        self.assertEqual(call.call_args.args[1], "hosted-quota-key")

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

    def test_sdk_diagnostics_allow_only_known_error_types_and_numeric_status(self):
        import httpx
        from openai import APIConnectionError, APIStatusError, APITimeoutError

        secret_key = "private-key-sentinel"
        secret_body = "private-upstream-body-sentinel"
        secret_header = "private-header-sentinel"
        secret_input = "private-request-text-sentinel"
        request = httpx.Request("POST", "https://hosted.example/v1/chat/completions",
                                headers={"Authorization": "Bearer " + secret_key}, content=secret_input)
        cases = [(APITimeoutError(request=request), "APITimeoutError"),
                 (APIConnectionError(message=secret_body, request=request), "APIConnectionError")]
        for status in (401, 403, 429, 503):
            response = httpx.Response(status, request=request, headers={"x-private": secret_header},
                                      json={"error": secret_body})
            cases.append((APIStatusError(secret_body, response=response, body={"secret": secret_body}), f"HTTP {status}"))
        nonnumeric_status = RuntimeError(secret_body)
        nonnumeric_status.status_code = secret_header
        cases.append((nonnumeric_status, "could not complete"))
        for error, classification in cases:
            with self.subTest(classification=classification):
                client = Mock()
                client.chat.completions.create.side_effect = error
                with patch("openai.OpenAI", return_value=client) as sdk:
                    with self.assertRaises(ASIError) as caught:
                        _sdk_completion({"messages": [{"role": "user", "content": secret_input}]},
                                        secret_key, "https://hosted.example/v1", 18.0)
                message = str(caught.exception)
                self.assertIn(classification, message)
                for secret in (secret_key, secret_body, secret_header, secret_input):
                    self.assertNotIn(secret, message)
                self.assertEqual(18.0, sdk.call_args.kwargs["timeout"])
                self.assertEqual(0, sdk.call_args.kwargs["max_retries"])
                client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
