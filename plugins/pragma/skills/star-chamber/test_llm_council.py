"""Tests for llm_council.py."""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_council import (
    DEFAULT_MAX_TOKENS,
    _get_review_internal,
    _resolve_platform_keys,
    resolve_api_keys,
    run_council,
)


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


class TestApiBasePassthrough:
    """Verify api_base from provider config is passed to acompletion."""

    def test_api_base_forwarded_to_acompletion(self):
        """api_base should be passed to acompletion when provided."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(
                _get_review_internal(
                    "llamafile", "local-model", "test prompt", "",
                    api_base="http://gpu-box.local:8080/v1",
                ),
            )
            assert mock_acompletion.call_args.kwargs.get("api_base") == "http://gpu-box.local:8080/v1"

    def test_api_base_omitted_when_empty(self):
        """api_base should not be in kwargs when empty or omitted."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(_get_review_internal("gemini", "gemini-2.5-flash", "test prompt", "key"))
            assert "api_base" not in mock_acompletion.call_args.kwargs

    def test_run_council_threads_api_base_from_provider(self):
        """run_council should read api_base from provider config and pass it through."""
        mock_acompletion = _mock_acompletion()
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        providers = [
            {"provider": "llamafile", "model": "local", "api_base": "http://localhost:8080/v1"},
            {"provider": "openai", "model": "gpt-5.2", "api_key": "k1"},
        ]

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            asyncio.run(run_council("test prompt", providers))
            calls_by_provider = {
                c.kwargs["provider"]: c.kwargs
                for c in mock_acompletion.call_args_list
            }
            # llamafile: api_base should be forwarded.
            assert calls_by_provider["llamafile"].get("api_base") == "http://localhost:8080/v1"
            # openai: no api_base in config, should not be in kwargs.
            assert "api_base" not in calls_by_provider["openai"]


def _mock_platform_client_module(mock_client_instance, fetch_error_cls):
    """Create a mock any_llm_platform_client module for patching into sys.modules."""
    mock_module = MagicMock()
    mock_module.AnyLLMPlatformClient = MagicMock(return_value=mock_client_instance)
    mock_module.ProviderKeyFetchError = fetch_error_cls
    return mock_module


# Shared exception class for platform client tests.
_ProviderKeyFetchError = type("ProviderKeyFetchError", (Exception,), {})


class TestResolvePlatformKeys:
    """Verify _resolve_platform_keys() fetches keys and handles local providers."""

    def test_successful_key_fetch(self):
        """Platform keys should be set on providers from fetched results."""
        mock_result = MagicMock()
        mock_result.api_key = "fetched-key-123"

        mock_client = MagicMock()
        mock_client.aget_decrypted_provider_key = AsyncMock(return_value=mock_result)

        providers = [
            {"provider": "openai", "model": "gpt-5.2", "api_key": ""},
        ]

        mock_mod = _mock_platform_client_module(mock_client, _ProviderKeyFetchError)
        with patch.dict(sys.modules, {"any_llm_platform_client": mock_mod}):
            result = asyncio.run(_resolve_platform_keys(providers, "test-key"))
            assert result[0]["api_key"] == "fetched-key-123"
            mock_client.aget_decrypted_provider_key.assert_awaited_once_with("test-key", "openai")

    def test_local_provider_tolerates_fetch_error(self):
        """Local providers should get empty api_key when platform fetch fails."""
        mock_client = MagicMock()
        mock_client.aget_decrypted_provider_key = AsyncMock(
            side_effect=_ProviderKeyFetchError("no key"),
        )

        providers = [
            {"provider": "llamafile", "model": "local-model", "api_key": "", "local": True},
        ]

        mock_mod = _mock_platform_client_module(mock_client, _ProviderKeyFetchError)
        with patch.dict(sys.modules, {"any_llm_platform_client": mock_mod}):
            result = asyncio.run(_resolve_platform_keys(providers, "test-key"))
            assert result[0]["api_key"] == ""

    def test_non_local_provider_raises_on_fetch_error(self):
        """Non-local providers should re-raise ProviderKeyFetchError."""
        mock_client = MagicMock()
        mock_client.aget_decrypted_provider_key = AsyncMock(
            side_effect=_ProviderKeyFetchError("no key"),
        )

        providers = [
            {"provider": "openai", "model": "gpt-5.2", "api_key": ""},
        ]

        mock_mod = _mock_platform_client_module(mock_client, _ProviderKeyFetchError)
        with patch.dict(sys.modules, {"any_llm_platform_client": mock_mod}):
            with pytest.raises(_ProviderKeyFetchError):
                asyncio.run(_resolve_platform_keys(providers, "test-key"))


class TestResolveApiKeysDirectMode:
    """Verify resolve_api_keys() in direct mode preserves local field."""

    def test_local_field_preserved_in_direct_mode(self):
        """The local field should pass through env var expansion unchanged."""
        providers = [
            {"provider": "llamafile", "model": "local", "api_key": "", "local": True},
            {"provider": "openai", "model": "gpt-5.2", "api_key": "${OPENAI_API_KEY}"},
        ]
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = resolve_api_keys(providers, use_platform=False)
            assert result[0]["local"] is True
            assert result[1]["api_key"] == "sk-test"
            assert result[0]["api_key"] == ""

    def test_local_field_preserved_in_platform_mode(self):
        """Platform mode should clear api_key but keep local field."""
        providers = [
            {"provider": "llamafile", "model": "local", "api_key": "", "local": True},
        ]
        result = resolve_api_keys(providers, use_platform=True)
        assert result[0]["local"] is True
        assert result[0]["api_key"] == ""


class TestLocalProviderErrorMessage:
    """Verify local providers get better auth error messages."""

    def test_local_provider_auth_error_message(self):
        """Local provider auth errors should suggest platform or providers.json."""
        mock_acompletion = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            result = asyncio.run(
                _get_review_internal("llamafile", "local-model", "test", "", local=True)
            )
            assert not result["success"]
            assert "Local provider llamafile" in result["error"]
            assert "providers.json" in result["error"]

    def test_non_local_provider_auth_error_unchanged(self):
        """Non-local provider auth errors should keep the standard message."""
        mock_acompletion = AsyncMock(side_effect=Exception("401 Unauthorized"))
        mock_module = MagicMock()
        mock_module.acompletion = mock_acompletion

        with patch.dict(sys.modules, {"any_llm": mock_module}):
            result = asyncio.run(
                _get_review_internal("openai", "gpt-5.2", "test", "", local=False)
            )
            assert not result["success"]
            assert "Authentication failed for openai" in result["error"]


class TestListSdksLocalProviders:
    """Verify --list-sdks output categorizes local providers correctly."""

    def test_local_providers_not_in_missing_key(self, tmp_path):
        """Local providers should appear in providers_local, not providers_missing_key."""
        from llm_council import main
        import io

        config = {
            "providers": [
                {"provider": "openai", "model": "gpt-5.2", "api_key": "${OPENAI_API_KEY}"},
                {"provider": "llamafile", "model": "local", "api_base": "http://localhost:8080/v1", "local": True},
            ],
        }
        config_file = tmp_path / "providers.json"
        config_file.write_text(json.dumps(config))

        with (
            patch("llm_council.load_sdk_map", return_value={"anthropic": "anthropic"}),
            patch("sys.argv", ["llm_council.py", "--list-sdks"]),
            pytest.raises(SystemExit) as exc_info,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch.dict(os.environ, {"OPENAI_API_KEY": "", "STAR_CHAMBER_CONFIG": str(config_file)}, clear=False),
        ):
            main()

        assert exc_info.value.code == 0
        output = json.loads(mock_stdout.getvalue())
        assert "llamafile" in output["providers_local"]
        assert "llamafile" not in output["providers_missing_key"]
        assert "openai" in output["providers_missing_key"]
