import base64
import json
import re
from hashlib import sha256
from pathlib import Path

import pymupdf

PAR_APPEL = 8

CONSIGNE = """Tu reçois les images de plusieurs slides d'un pitch deck, chacune précédée de son titre "## Slide N".
Pour chaque slide, recopie son titre "## Slide N" puis, en dessous, décris tout ce qu'elle contient :

- Graphiques : indique le type de graphique, ce que représentent les axes, leur unité et leur échelle (ex : "en milliers"), puis chaque valeur lisible avec son libellé.
- Tableaux et schémas : indique les correspondances (quelle valeur va avec quelle ligne ou colonne, flèches, étapes).
- Logos et photos : cite les noms de sociétés et de personnes visibles, et leur rôle sur la slide (clients, partenaires, investisseurs, équipe).
- Mises en avant visuelles : signale les éléments cochés, barrés, surlignés ou encadrés (ex : tableau concurrentiel).

Recopie chaque chiffre exactement comme affiché, avec son unité, sa devise et sa période (ex : "1,2M €", "15% MoM", "2024").
N'interprète rien, ne résume rien, n'invente rien. Si un élément est illisible, écris [illisible].
Réponds uniquement avec les titres et les descriptions, sans phrase d'introduction."""


def images_pdf(chemin):
    with pymupdf.open(chemin) as doc:
        return [page.get_pixmap(dpi=150).tobytes("png") if page.get_images() or page.get_drawings() else None for page in doc]


def texte_pdf(chemin):
    with pymupdf.open(chemin) as doc:
        return [page.get_text() for page in doc]


def ocr_pdf(client, chemin):
    with open(chemin, "rb") as fichier:
        pdf_b64 = base64.b64encode(fichier.read()).decode()
    reponse = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": f"data:application/pdf;base64,{pdf_b64}"},
    )
    return [page.markdown for page in reponse.pages]


def transcrire_images(client, images):
    visuelles = [(i + 1, image) for i, image in enumerate(images) if image]
    descriptions = {}
    for debut in range(0, len(visuelles), PAR_APPEL):
        contenu = [{"type": "text", "text": CONSIGNE}]
        for numero, image in visuelles[debut:debut + PAR_APPEL]:
            contenu += [
                {"type": "text", "text": f"## Slide {numero}"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image).decode()}"}},
            ]
        reponse = client.chat.complete(model="mistral-medium-latest", messages=[{"role": "user", "content": contenu}])
        texte = reponse.choices[0].message.content
        descriptions.update({int(numero): description.strip() for numero, description in re.findall(r"^\W*Slide (\d+)\W*$(.*?)(?=^\W*Slide \d+\W*$|\Z)", texte, re.S | re.M)})
    return descriptions


def lire_deck(client, chemin):
    cache = Path("cache") / f"{sha256(Path(chemin).read_bytes() + CONSIGNE.encode()).hexdigest()[:16]}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    images = images_pdf(chemin)
    try:
        textes = ocr_pdf(client, chemin)
    except Exception as erreur:
        print(f"OCR indisponible ({erreur})")
        textes, cache = ["[OCR indisponible]"] * len(images), None
    textes_pdf = texte_pdf(chemin)
    descriptions = transcrire_images(client, images)
    slides = [{"numero": i + 1, "texte_ocr": textes[i], "texte_pdf": textes_pdf[i], "texte_vision": descriptions.get(i + 1, "[non décrit]" if image else "[aucun élément visuel]")} for i, image in enumerate(images)]
    if cache:
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(slides, ensure_ascii=False), encoding="utf-8")
    return slides
