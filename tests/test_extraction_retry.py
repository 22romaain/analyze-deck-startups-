"""Tests du réessai Mistral (_complete_with_retry) : rate limit géré sans API ni attente."""

import pytest

from src.extraction import _complete_with_retry, _is_retryable


class _RateLimitError(Exception):
    """Simule une erreur de rate limit avec un status_code, comme le SDK."""
    status_code = 429


class _FakeChat:
    def __init__(self, fails_before_success: int, exc: Exception):
        self.calls = 0
        self.fails_before_success = fails_before_success
        self.exc = exc

    def complete(self, model, messages):
        self.calls += 1
        if self.calls <= self.fails_before_success:
            raise self.exc
        return "OK"


class _FakeClient:
    def __init__(self, chat):
        self.chat = chat


def test_is_retryable_reconnait_le_rate_limit():
    assert _is_retryable(_RateLimitError()) is True
    assert _is_retryable(Exception("Rate limit exceeded")) is True
    assert _is_retryable(Exception("invalid api key")) is False


def test_retry_reussit_apres_deux_rate_limits():
    # Echoue 2 fois (rate limit) puis reussit : le wrapper doit finir par renvoyer OK.
    client = _FakeClient(_FakeChat(fails_before_success=2, exc=_RateLimitError()))
    waits: list = []
    result = _complete_with_retry(client, "m", [], sleep=waits.append)
    assert result == "OK"
    assert client.chat.calls == 3
    assert waits == [20, 40]  # a patiente avant les 2 reessais


def test_erreur_non_retryable_remonte_immediatement():
    # Une cle invalide n'est pas transitoire : pas de reessai, l'erreur remonte.
    client = _FakeClient(_FakeChat(fails_before_success=99, exc=Exception("invalid api key")))
    with pytest.raises(Exception, match="invalid api key"):
        _complete_with_retry(client, "m", [], sleep=lambda s: None)
    assert client.chat.calls == 1


def test_abandon_apres_tous_les_reessais():
    # Rate limit permanent : apres tous les essais, on leve une erreur explicite.
    client = _FakeClient(_FakeChat(fails_before_success=99, exc=_RateLimitError()))
    with pytest.raises(RuntimeError, match="rate limit"):
        _complete_with_retry(client, "m", [], sleep=lambda s: None)
    assert client.chat.calls == 4  # 1 initial + 3 reessais
