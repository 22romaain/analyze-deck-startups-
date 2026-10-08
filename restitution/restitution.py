from markdown_pdf import MarkdownPdf, Section


def restituer(fiche, analyse):
    lignes = ["# Mémo d'analyse"]
    for dimension in analyse.dimensions:
        lignes += ["", f"## {dimension.nom}"]
        for champ, points in dimension.model_dump(exclude={"nom"}).items():
            if points:
                lignes += ["", f"### {champ.replace('_', ' ').capitalize()}", *(f"- {point}" for point in points)]
    lignes += ["", "## Annexe : fiche du deck", "", "```json", fiche.model_dump_json(indent=2, exclude_none=True), "```"]
    return "\n".join(lignes)


def en_pdf(texte, chemin):
    pdf = MarkdownPdf()
    pdf.add_section(Section(texte))
    pdf.save(chemin)
