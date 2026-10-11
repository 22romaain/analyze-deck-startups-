from markdown_pdf import MarkdownPdf, Section

METHODOLOGIE = """## Annexe : méthodologie

**Comment le deck est lu.** Chaque slide est lue de trois façons indépendantes : le texte intégré au PDF, une reconnaissance de caractères (OCR) sur l'image de la slide, et une description par un modèle de vision qui relève les graphiques, tableaux, logos et éléments mis en avant. Les trois lectures sont recoupées pour ne rien manquer, en particulier les chiffres qui n'apparaissent que dans des images.

**Comment la fiche est remplie.** Un modèle d'IA range toutes les informations du deck dans une fiche standard, quelle que soit la slide où elles apparaissent. Il ne calcule rien, ne déduit rien et n'invente rien : ce que le deck ne dit pas reste vide, et ce que la société affirme reste une affirmation. Les chiffres prévisionnels sont séparés des chiffres réels, et les contradictions entre slides sont relevées.

**Ce que couvre la fiche.** L'identité de la société et son stade, le problème traité, le produit, le marché, la concurrence et ce qui la protège, la traction (chiffre d'affaires, clients, rétention), l'acquisition et la monétisation, les coûts, la trésorerie et le prévisionnel, l'équipe, le deal et la table de capitalisation, la sortie envisagée, l'ESG et les références. Selon le modèle d'affaires, la fiche ajoute des rubriques spécifiques : revenu récurrent pour un SaaS, liquidité pour une marketplace, entonnoir d'acquisition pour un produit grand public, data et technologie quand le deck en parle.

**Comment l'analyse est faite.** La fiche est comparée à un référentiel construit à partir des grilles utilisées par les fonds (Point Nine, Sequoia, les 4M de Partech) et de repères chiffrés publiés (Bessemer, Carta, a16z, David Sacks, Dealroom), ajustés selon le stade et le modèle d'affaires. Pour chaque dimension, l'analyse sépare les forces, les faiblesses, les informations manquantes et les points à vérifier auprès des fondateurs. Chaque repère cité indique sa source et son année.

**Ce que le mémo ne fait pas.** Il ne donne ni note, ni score, ni recommandation d'investir : il décrit ce que montre le deck et ce qu'il faut creuser. Une information absente n'est pas un défaut mais une question à poser. Le mémo repose uniquement sur le deck : aucune information n'est vérifiée auprès de sources externes."""


def restituer(analyse):
    lignes = ["# Mémo d'analyse"]
    for dimension in analyse.dimensions:
        lignes += ["", f"## {dimension.nom}"]
        for champ, points in dimension.model_dump(exclude={"nom"}).items():
            if points:
                lignes += ["", f"### {champ.replace('_', ' ').capitalize()}", *(f"- {point}" for point in points)]
    lignes += ["", METHODOLOGIE]
    return "\n".join(lignes)


def en_pdf(texte, chemin):
    pdf = MarkdownPdf()
    pdf.add_section(Section(texte))
    pdf.save(chemin)
