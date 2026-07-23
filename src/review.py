"""Contre-analyse LLM (avocat du diable) pour la section 6 du mémo.

Un associé VC sceptique challenge l'analyse déterministe : angles morts, raisons de
passer, points trop généreux. Explicitement HORS score et non reproductible (c'est
un avis LLM). Robuste : toute erreur renvoie None -> le mémo garde son mode dégradé.
"""

import os
import re
from pathlib import Path

from mistralai.client import Mistral

from src.extraction import TEXT_MODEL, _complete_with_retry
from src.models import DeckAnalysis, AnalysisResult

REVIEW_SYSTEM_PROMPT = (
    "Tu es un associé VC senior et sceptique qui joue l'avocat du diable. On te donne "
    "l'analyse d'un pitch deck. Écris une contre-analyse courte et lucide : les angles "
    "morts, les raisons sérieuses de passer, les points où l'analyse est peut-être trop "
    "généreuse, et 2 à 3 risques sous-estimés. Sois concret et spécifique au dossier, ne "
    "répète pas l'analyse, challenge-la. 150 à 250 mots, en français, pas de JSON."
)

# Thèse d'investissement (canal 2) : prose libre éditée à la main par le créateur de
# l'app. Injectée dans le prompt de la contre-analyse pour confronter le deck à sa thèse.
THESE_PATH = Path(__file__).resolve().parent.parent / "config" / "these_investissement.md"


def charger_these(path: Path = THESE_PATH) -> str:
    """Lit la thèse d'investissement si elle existe, sinon chaîne vide.

    Les blocs de commentaire HTML (les consignes du gabarit) sont retirés : tant que
    l'utilisateur n'a rien écrit sous ces consignes, la thèse est vide et rien n'est
    injecté. Fichier absent ou illisible = pas d'injection, la contre-analyse tourne.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL).strip()


def _summarize(deck: DeckAnalysis, analysis: AnalysisResult) -> str:
    """Résumé compact de l'analyse à soumettre à l'avocat du diable.

    Sans score (l'outil n'en produit plus) : on donne les constats déterministes (red
    flags, incohérences, cap table) et le récit du deck, pas de note chiffrée.
    """
    flags = "\n".join(f"- [{f.severity}] {f.dimension} : {f.message}"
                      for f in analysis.red_flags) or "- aucun"
    return (
        f"Société : {deck.company_name or 'inconnue'}\n"
        f"Round : {analysis.round} | Ask : {deck.ask_amount}\n\n"
        f"Red flags et constats déterministes détectés :\n{flags}\n\n"
        f"Analyse narrative :\n"
        f"Équipe : {deck.equipe}\nProblème : {deck.probleme}\nMarché : {deck.marche}\n"
        f"Traction : {deck.traction}\nBusiness model : {deck.business_model}\n"
        f"Concurrence : {deck.concurrence}\nAsk : {deck.ask}"
    )


def generate_review(
    client, deck: DeckAnalysis, analysis: AnalysisResult,
    complete=_complete_with_retry, these: str | None = None,
) -> str | None:
    """Contre-analyse LLM, ou None si l'appel échoue (le mémo reste en mode dégradé).

    complete injectable pour tester sans API. `these` = thèse d'investissement à
    confronter au deck (None -> chargée depuis le fichier). Toute exception est
    absorbée : la contre-analyse est un bonus, jamais un point de rupture du pipeline.
    """
    these_txt = charger_these() if these is None else these
    system = REVIEW_SYSTEM_PROMPT
    if these_txt:
        system += (
            "\n\nTu tiens compte de la thèse d'investissement du créateur de l'app "
            "ci-dessous. Confronte explicitement le deck à cette thèse : est-il aligné, "
            "en tension avec elle, ou hors de son périmètre ?\n\n"
            f"Thèse d'investissement :\n{these_txt}"
        )
    messages = [
        {"role": "system", "content": system},
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
