import io
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qa import llm


class TestLLMConfiguration(unittest.TestCase):
    def test_false_mock_values_use_real_provider(self):
        for value in ("0", "false", "no", "off"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {
                    "QA_MOCK": value,
                    "LLM_PROVIDER": "openai",
                    "OPENAI_API_KEY": "test-key",
                }), patch("qa.llm._openai", return_value=("real response", {})) as openai_call:
                    result = llm.call_llm([], "test question")

                openai_call.assert_called_once()
                self.assertEqual(result["text"], "real response")

    def test_mock_error_modes_remain_enabled(self):
        with patch.dict(os.environ, {"QA_MOCK": "rate_limit"}):
            with self.assertRaises(llm.LLMError) as raised:
                llm.call_llm([], "test question")

        self.assertEqual(raised.exception.code, "rate_limit")

    def test_model_access_error_uses_active_provider_config(self):
        response = io.BytesIO(
            b'{"error":{"message":"model access denied"}}'
        )
        error = urllib.error.HTTPError(
            "https://api.groq.com", 403, "Forbidden", {}, response
        )

        with patch.dict(os.environ, {
            "LLM_PROVIDER": "groq",
            "GROQ_MODEL": "example-groq-model",
        }):
            result = llm._http_error(error)
        error.close()

        self.assertIn("GROQ_MODEL", result.message)
        self.assertIn("groq", result.message)
        self.assertNotIn("gpt-4o-mini", result.message)


if __name__ == "__main__":
    unittest.main()
