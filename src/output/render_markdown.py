"""Rendu Markdown du mémo qualitatif : mise en forme pure, aucun calcul.

Toute donnée affichée vient de `MemoData` (produit par memo_data.build_memo_data).
Ce module ne trie, ne compare, ne décide rien : il met en page. docx et pdf dérivent
de ce rendu, c'est donc la source de mise en forme du mémo.
"""

import re
from pathlib import Path

from src.models import FINDING_CATEGORIES, Finding
from src.output.memo_data import MemoData

# Dossier de sortie par défaut : output/ à la racine (rendu ignoré par git).
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"

# Libellés des statuts de la grille d'attendus. Pur affichage (le statut est calculé
# en amont), on ne fait que traduire l'énum en français.
STATUT_GRILLE_LABELS: dict[str, str] = {
    "PRESENT": "Présent",
    "ABSENT": "Absent (nié)",
    "INCONNU": "Inconnu",
}

# Valeur affichée quand une cellule est vide (None), pour garder le tableau lisible.
VIDE = "—"


def fmt_m(value: float) -> str:
    """Montant en millions, lisible (ex: 10000000 -> '10,0M'). Devise portée par le deck."""
    return f"{value / 1e6:.1f}M".replace(".", ",")


def _finding_line(finding: Finding) -> str:
    """Un constat en une ligne de liste : sa catégorie lisible puis son message."""
    label = FINDING_CATEGORIES[finding.categorie]["label"]
    return f"- **{label}** — {finding.message}"


def _render_header(memo: MemoData) -> list[str]:
    """En-tête : société, round, montant, date, puis le disclaimer."""
    return [
        f"# Mémo d'investissement — {memo.societe}",
        "",
        f"- **Round** : {memo.round}",
        f"- **Montant recherché** : {memo.ask_amount}",
        f"- **Date** : {memo.date.isoformat()}",
        "",
        f"> {memo.disclaimer}",
    ]


def _render_recommandation(memo: MemoData) -> list[str]:
    """Section 1 : la recommandation qualitative et sa justification (sans score)."""
    r = memo.synthese.recommandation
    return [
        f"## Recommandation : {r.decision}",
        "",
        r.justification,
        "",
        f"- Rédhibitoires : {r.nb_redhibitoires} · Faiblesses : {r.nb_faiblesses} · Atouts : {r.nb_atouts}",
    ]


def _render_synthese(memo: MemoData) -> list[str]:
    """Section 2 : synthèse pros/cons, les constats groupés par polarité."""
    s = memo.synthese
    lines = ["## Synthèse", "", "### Atouts"]
    lines += [_finding_line(f) for f in s.atouts] or ["_Aucun atout relevé._"]
    lines += ["", "### Points négatifs"]
    lines += [_finding_line(f) for f in s.points_negatifs] or ["_Aucun point négatif relevé._"]
    if s.a_creuser:
        lines += ["", "### À creuser"]
        lines += [_finding_line(f) for f in s.a_creuser]
    return lines


def _render_grille(memo: MemoData) -> list[str]:
    """Section 3 : grille d'attendus du round (présent / absent / inconnu)."""
    if not memo.grille:
        return []
    lines = [
        "## Grille d'attendus",
        "",
        "| Attendu | Statut | Valeur | Criticité |",
        "| --- | --- | --- | --- |",
    ]
    for row in memo.grille:
        valeur = row.valeur if row.valeur is not None else VIDE
        lines.append(f"| {row.label} | {STATUT_GRILLE_LABELS[row.statut]} | {valeur} | {row.criticite} |")
    return lines


def _render_deck_figures(memo: MemoData) -> list[str]:
    """Section 'ce que le deck affirme' : inventaire brut. Absent si le deck n'a aucun chiffre."""
    if not memo.chiffres_deck:
        return []
    lines = ["## Ce que le deck affirme", "",
             "| Métrique | Valeur | Période | Source |", "| --- | --- | --- | --- |"]
    for row in memo.chiffres_deck:
        periode = row.periode if row.periode else VIDE
        source = f"slide {row.slide}" if row.slide is not None else VIDE
        lines.append(f"| {row.libelle} | {row.valeur} | {periode} | {source} |")
    return lines


def _render_dimensions(memo: MemoData) -> list[str]:
    """Section 4 : analyse par dimension (récit du deck + constats, sans score)."""
    lines = ["## Analyse par dimension"]
    for d in memo.dimensions:
        lines += ["", f"### {d.label}"]
        if d.narratif:
            lines += ["", "Ce que dit le deck :", d.narratif]
        if d.findings:
            lines += ["", "Constats :"]
            lines += [_finding_line(f) for f in d.findings]
        if d.doctrine:
            lines += ["", "Doctrine VC :"]
            lines += [f"- ({c.source}, §{c.section}) {c.extrait}" for c in d.doctrine]
    return lines


def _render_incoherences(memo: MemoData) -> list[str]:
    """Section 5 : incohérences internes (chiffres qui se contredisent). Absente si aucune."""
    if not memo.incoherences:
        return []
    return ["## Incohérences internes", ""] + [_finding_line(f) for f in memo.incoherences]


def _render_review(memo: MemoData) -> list[str]:
    """Section 6 : lecture LLM au regard de la thèse. Encart distinct, mode dégradé géré."""
    r = memo.contre_analyse
    lines = ["## Analyse au regard de ta thèse", "", f"> {r.bandeau}"]
    if r.disponible and r.contenu:
        lines += ["", r.contenu]
    return lines


def _render_captable(memo: MemoData) -> list[str]:
    """Section 7 : cap table et dilution. Encart dégradé si les termes manquent."""
    c = memo.cap_table
    lines = ["## Cap table et dilution", ""]
    if not c.calculable:
        lines.append("_Non calculable._ Termes manquants ou incohérents :")
        lines += [f"- {d}" for d in c.donnees_absentes]
        return lines
    d = c.dilution
    lines += [
        f"- **Pre-money** : {fmt_m(c.pre_money)}",
        f"- **Montant levé** : {fmt_m(c.amount)}",
        f"- **Post-money** : {fmt_m(d.post_money)}",
        f"- **Nouvel investisseur** : {d.new_investor_pct:.0f}%",
    ]
    if d.option_pool_pct > 0:
        lines.append(f"- **Option pool créé** : {d.option_pool_pct:.0f}%")
    lines.append(
        f"- **Fondateurs** : {c.founder_pct_pre:.0f}% → **{d.founder_pct_post:.0f}%** "
        f"(dilution de {d.founder_dilution_points:.0f} pts)"
    )
    if c.waterfall is not None:
        w = c.waterfall
        lines += [
            "", "### Waterfall (sortie au post-money)",
            f"À une sortie à {fmt_m(w.exit_value)}, les fondateurs touchent "
            f"**{w.founders_pct_of_exit:.0f}%** (~{fmt_m(w.founders_payout)}).",
        ]
    return lines


def _render_annexes(memo: MemoData) -> list[str]:
    """Section 8 : méthodologie, limites, extraction brute."""
    a = memo.annexes
    lines = ["## Annexes", "", "### Méthodologie", a.methodologie,
             "", "### Limites", a.limites, "", "### Extraction brute"]
    for key, value in a.extraction_brute.items():
        lines.append(f"- **{key}** : {value}")
    return lines


def render_markdown(memo: MemoData) -> str:
    """Assemble le mémo complet en Markdown.

    Les sections sont séparées par une ligne vide. Le document se termine par un
    retour à la ligne unique (convention fichier texte).
    """
    blocks = [
        _render_header(memo),
        _render_recommandation(memo),
        _render_synthese(memo),
        _render_grille(memo),
        _render_deck_figures(memo),
        _render_dimensions(memo),
        _render_incoherences(memo),
        _render_review(memo),
        _render_captable(memo),
        _render_annexes(memo),
    ]
    # On écarte les blocs vides (section optionnelle absente) pour ne pas insérer de
    # ligne blanche parasite.
    blocks = [b for b in blocks if b]
    lines: list[str] = []
    for i, block in enumerate(blocks):
        lines += block
        if i < len(blocks) - 1:
            lines.append("")  # ligne vide entre sections
    return "\n".join(lines) + "\n"


def _slugify(name: str) -> str:
    """Nom de fichier sûr : lettres/chiffres, le reste devient '_'."""
    slug = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_")
    return slug or "societe"


def output_path(memo: MemoData, extension: str, output_dir: Path | None = None) -> Path:
    """Chemin de sortie partagé par les renderers : memo_{societe}_{date}.{ext}."""
    directory = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"memo_{_slugify(memo.societe)}_{memo.date.isoformat()}.{extension}"


def write_markdown(memo: MemoData, output_dir: Path | None = None) -> Path:
    """Écrit le mémo Markdown sur disque et retourne le chemin. Erreur claire si échec."""
    path = output_path(memo, "md", output_dir)
    try:
        path.write_text(render_markdown(memo), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Écriture du mémo Markdown impossible ({path}) : {exc}") from exc
    return path
