"""Tests for llm_council.py."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from llm_council import DEFAULT_MAX_TOKENS, _get_review_internal, run_council


def _mock_acompletion():
    """Create a mock acompletion that returns a valid response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"provider": "test"}'
    return AsyncMock(return_value=mock_response)


class TestMaxTokensPassthrough:
    """Verify max_tokens from provider config is passed to acompletion."""

    def test_default_max_tokens_passed_to_acompletion(self):
        """Default max_tokens should be used when provider config omits it."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        # Use gemini (non-OpenAI) to test the max_tokens path.
        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(_get_review_internal("gemini", "gemini-2.5-flash", "test prompt", "key"))
            assert mock_acompletion.call_args.kwargs.get("max_tokens") == DEFAULT_MAX_TOKENS

    def test_custom_max_tokens_passed_to_acompletion(self):
        """Provider-specified max_tokens should override the default."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(_get_review_internal("anthropic", "claude-opus-4-6", "test prompt", "key", max_tokens=8192))
            assert mock_acompletion.call_args.kwargs.get("max_tokens") == 8192

    def test_openai_uses_max_completion_tokens(self):
        """OpenAI provider should use max_completion_tokens instead of max_tokens."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(_get_review_internal("openai", "gpt-5.2", "test prompt", "key", max_tokens=128000))
            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs.get("max_completion_tokens") == 128000
            assert "max_tokens" not in call_kwargs

    def test_run_council_threads_max_tokens_from_provider(self):
        """run_council should read max_tokens from provider config and pass it through."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        providers = [
            {"provider": "openai", "model": "gpt-5.2", "api_key": "k1", "max_tokens": 128000},
            {"provider": "gemini", "model": "gemini-2.5-flash", "api_key": "k2", "max_tokens": 65536},
            {"provider": "anthropic", "model": "claude-opus-4-6", "api_key": "k3"},
        ]

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(run_council("test prompt", providers))
            # Index calls by provider to avoid order-dependent assertions.
            calls_by_provider = {
                c.kwargs["provider"]: c.kwargs
                for c in mock_acompletion.call_args_list
            }
            # openai: explicit 128000 via max_completion_tokens.
            assert calls_by_provider["openai"].get("max_completion_tokens") == 128000
            assert "max_tokens" not in calls_by_provider["openai"]
            # gemini: explicit 65536 via max_tokens.
            assert calls_by_provider["gemini"].get("max_tokens") == 65536
            # anthropic: no max_tokens in config, should get default.
            assert calls_by_provider["anthropic"].get("max_tokens") == DEFAULT_MAX_TOKENS
