"""Contre-analyse LLM (avocat du diable) pour la section 6 du mémo.

Un associé VC sceptique challenge l'analyse déterministe : angles morts, raisons de
passer, points trop généreux. Explicitement HORS score et non reproductible (c'est
un avis LLM). Robuste : toute erreur renvoie None -> le mémo garde son mode dégradé.
"""

import os

from mistralai.client import Mistral

from src.extraction import TEXT_MODEL, _complete_with_retry
from src.models import DeckAnalysis, AnalysisResult

REVIEW_SYSTEM_PROMPT = (
    "Tu es un associé VC senior et sceptique qui joue l'avocat du diable. On te donne "
    "l'analyse d'un pitch deck. Écris une contre-analyse courte et lucide : les angles "
    "morts, les raisons sérieuses de PASSER, les points où l'analyse est peut-être trop "
    "généreuse, et 2 à 3 risques sous-estimés. Sois concret et spécifique au dossier, ne "
    "répète pas l'analyse, challenge-la. 150 à 250 mots, en français, pas de JSON."
)


def _summarize(deck: DeckAnalysis, analysis: AnalysisResult) -> str:
    """Résumé compact de l'analyse à soumettre à l'avocat du diable."""
    flags = "\n".join(f"- [{f.severity}] {f.dimension} : {f.message}"
                      for f in analysis.red_flags) or "- aucun"
    scores = "\n".join(f"- {d.label} : {d.score:.0f}/100" for d in analysis.dimension_scores)
    return (
        f"Société : {deck.company_name or 'inconnue'}\n"
        f"Round : {analysis.round} | Ask : {deck.ask_amount}\n"
        f"Score global : {analysis.global_score:.0f}/100\n\n"
        f"Red flags détectés :\n{flags}\n\n"
        f"Scores par dimension :\n{scores}\n\n"
        f"Analyse narrative :\n"
        f"Équipe : {deck.equipe}\nProblème : {deck.probleme}\nMarché : {deck.marche}\n"
        f"Traction : {deck.traction}\nBusiness model : {deck.business_model}\n"
        f"Concurrence : {deck.concurrence}\nAsk : {deck.ask}"
    )


def generate_review(client, deck: DeckAnalysis, analysis: AnalysisResult, complete=_complete_with_retry) -> str | None:
    """Contre-analyse LLM, ou None si l'appel échoue (le mémo reste en mode dégradé).

    complete injectable pour tester sans API. Toute exception est absorbée : la
    contre-analyse est un bonus, jamais un point de rupture du pipeline.
    """
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": _summarize(deck, analysis)},
    ]
    try:
        response = complete(client, TEXT_MODEL, messages)
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        return None


def make_review_generator():
    """Générateur de contre-analyse fermé sur un client Mistral, ou None si pas de clé.

    None -> la CLI passe simplement au mode dégradé, sans erreur.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return None
    client = Mistral(api_key=api_key)

    def generate(deck: DeckAnalysis, analysis: AnalysisResult) -> str | None:
        return generate_review(client, deck, analysis)

    return generate
