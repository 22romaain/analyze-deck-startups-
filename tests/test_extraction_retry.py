"""Tests du réessai Mistral (_complete_with_retry) : rate limit géré sans API ni attente."""

import pytest

from src.extraction import _complete_with_retry, _extract_analysis, _is_retryable, _parse_response


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


# --- Robustesse du JSON renvoye ---

import json as _json


def _valid_deck_json() -> str:
    dims = {d: "texte" for d in ["equipe", "probleme", "solution", "marche", "business_model",
                                 "traction", "concurrence", "go_to_market", "financials", "ask"]}
    dims["detected_round"] = "serie-a"
    dims["ask_amount"] = "8M USD"
    return _json.dumps(dims)


def test_parse_response_ignore_le_preambule():
    # Le modele bavarde avant/apres le JSON : on ne garde que le bloc { ... }.
    raw = "Voici le JSON demande :\n" + _valid_deck_json() + "\nJ'espere que ca aide."
    analysis, _ = _parse_response(raw)
    assert analysis.detected_round == "serie-a"


class _Msg:
    def __init__(self, content): self.message = type("M", (), {"content": content})()


class _Resp:
    def __init__(self, content): self.choices = [_Msg(content)]


def test_extract_analysis_retente_sur_json_casse():
    # 1er appel : JSON casse (virgule manquante) ; 2e : JSON valide -> doit reussir.
    outputs = ['{"equipe": "x" "probleme": "y"}', _valid_deck_json()]

    class _Chat:
        def __init__(self): self.calls = 0
        def complete(self, model, messages):
            out = outputs[self.calls]; self.calls += 1
            return _Resp(out)

    client = _FakeClient(_Chat())
    analysis, _ = _extract_analysis(client, "m", [])
    assert analysis.detected_round == "serie-a"
    assert client.chat.calls == 2
