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

JUGE_SYSTEM_PROMPT = (
    "Tu es un associé VC senior. On te donne l'analyse factuelle d'un pitch deck, la "
    "thèse d'investissement du fonds, et des extraits de sa doctrine (cours). Produis "
    "DEUX volets, en français, sans JSON, sous ces intitulés exacts en gras :\n\n"
    "**Lecture au regard de ta thèse.** "
    "En quoi ce deck est aligné, en tension, ou hors périmètre par rapport à la thèse et "
    "aux principes de la doctrine fournie. Appuie-toi EXPLICITEMENT sur la thèse et les "
    "extraits de cours donnés (cite l'idée que tu appliques), jamais sur des généralités.\n\n"
    "**Contre-analyse.** "
    "L'avocat du diable : angles morts, raisons sérieuses de douter, points où l'analyse "
    "est trop généreuse, 2 à 3 risques sous-estimés. Challenge le dossier, y compris au "
    "regard de la thèse.\n\n"
    "Concret et spécifique au deck. 200 à 350 mots au total."
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


def rassembler_contexte_cours(
    retriever, requetes: list[str], max_chars: int = 1500
) -> tuple[str, list]:
    """Récupère les extraits de cours pertinents et les assemble en bloc de contexte LLM.

    Le bloc est la doctrine que le LLM doit appliquer (pas une citation décorative).
    Dédoublonne par (source, section), respecte un budget de caractères (les cours sont
    volumineux, on ne peut pas tout envoyer), et renvoie aussi les citations retenues pour
    afficher la provenance. retriever None -> ('', []) : le jugement tourne sans cours.
    """
    if retriever is None:
        return "", []
    # Import différé : évite de coupler ce module à la couche mémo au chargement.
    from src.output.memo_data import cite_doctrine

    vues: set[tuple[str, str]] = set()
    citations = []
    for requete in requetes:
        for cit in cite_doctrine(requete, retriever=retriever):
            cle = (cit.source, cit.section)
            if cle not in vues:
                vues.add(cle)
                citations.append(cit)

    morceaux: list[str] = []
    total = 0
    for cit in citations:
        ligne = f"[{cit.source} §{cit.section}] {cit.extrait}"
        if total + len(ligne) > max_chars:
            break
        morceaux.append(ligne)
        total += len(ligne)
    return "\n".join(morceaux), citations[:len(morceaux)]


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


def _build_system(these: str, contexte_cours: str) -> str:
    """Assemble le prompt système : la lentille (thèse + doctrine) autour du rôle du juge."""
    prompt = JUGE_SYSTEM_PROMPT
    if these:
        prompt += f"\n\nThèse d'investissement du fonds :\n{these}"
    if contexte_cours:
        prompt += f"\n\nDoctrine à appliquer (extraits de cours) :\n{contexte_cours}"
    if not these and not contexte_cours:
        prompt += ("\n\n(Aucune thèse ni doctrine fournie : tiens-t'en à une contre-analyse "
                   "générale, n'invente pas de thèse.)")
    return prompt


def generate_review(
    client, deck: DeckAnalysis, analysis: AnalysisResult,
    complete=_complete_with_retry, these: str | None = None, contexte_cours: str = "",
) -> str | None:
    """Jugement LLM combiné (lecture au regard de la thèse + contre-analyse), ou None si échec.

    complete injectable pour tester sans API. `these` = thèse (None -> chargée du fichier) ;
    `contexte_cours` = bloc de doctrine issu de rassembler_contexte_cours. Toute exception
    est absorbée : ce jugement est consultatif, jamais un point de rupture du pipeline, et
    le mémo garde son mode dégradé.
    """
    these_txt = charger_these() if these is None else these
    messages = [
        {"role": "system", "content": _build_system(these_txt, contexte_cours)},
        {"role": "user", "content": _summarize(deck, analysis)},
    ]
    try:
        response = complete(client, TEXT_MODEL, messages)
        text = (response.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        return None


def _requetes_doctrine(analysis: AnalysisResult, these: str) -> list[str]:
    """Requêtes RAG pour rassembler la doctrine à appliquer : les dimensions décisives
    du round (via ROUND_WEIGHTS) plus la thèse elle-même, bornée."""
    from src.analysis import ROUND_WEIGHTS
    from src.output.memo_data import DIMENSION_DOCTRINE_QUERY

    poids = ROUND_WEIGHTS.get(analysis.round, {})
    top_dims = sorted(poids, key=lambda d: -poids[d])[:3]
    requetes = [DIMENSION_DOCTRINE_QUERY.get(d, d) for d in top_dims]
    if these:
        requetes.append(these[:300])
    return requetes


def make_review_generator(retriever=None):
    """Générateur de jugement LLM fermé sur un client Mistral, ou None si pas de clé.

    retriever (optionnel) = RAG des cours : sa présence fait entrer la doctrine dans le
    raisonnement. None -> jugement sans cours ; pas de clé -> None (mode dégradé, sans erreur).
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return None
    client = Mistral(api_key=api_key)

    def generate(deck: DeckAnalysis, analysis: AnalysisResult) -> str | None:
        these = charger_these()
        contexte, _ = rassembler_contexte_cours(retriever, _requetes_doctrine(analysis, these))
        return generate_review(client, deck, analysis, these=these, contexte_cours=contexte)

    return generate
