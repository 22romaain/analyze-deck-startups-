import base64

import pymupdf

CONSIGNE ="""Tu reçois l'image d'une slide de pitch deck. Transcris tout ce qu'elle contient, fidèlement.

- Texte : recopie tout le texte visible, mot pour mot, y compris les titres, les notes et les petites mentions.
- Chiffres : recopie chaque chiffre exactement comme écrit, avec son unité, sa devise et sa période (ex : "1,2M €", "15% MoM", "2024").
- Graphiques : indique le type de graphique, ce que représentent les axes, leur unité et leur échelle (ex : "en milliers"), puis chaque valeur lisible.
- Tableaux : recopie-les ligne par ligne.
- Logos et photos : cite les noms de sociétés et de personnes visibles.

N'interprète rien, ne résume rien, n'invente rien. Si un élément est illisible, écris [illisible].
Réponds uniquement avec la transcription, sans phrase d'introduction."""


def images_pdf(chemin):
    with pymupdf.open(chemin) as doc:
        liste_images = []
        for page in doc:
            image = page.get_pixmap(dpi=150).tobytes("png")
            liste_images.append(image)
    return liste_images


def ocr_pdf(client, chemin):
    with open(chemin, "rb") as fichier:
        pdf_b64 = base64.b64encode(fichier.read()).decode()
    reponse = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": f"data:application/pdf;base64,{pdf_b64}"},
    )
    return [page.markdown for page in reponse.pages]


def transcrire_image(client, image):
    image_b64 = base64.b64encode(image).decode()
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": CONSIGNE},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ],
    }]
    reponse = client.chat.complete(model="mistral-medium-latest", messages=messages)
    return reponse.choices[0].message.content


def lire_deck(client, chemin):
    images = images_pdf(chemin)
    textes = ocr_pdf(client, chemin)
    slides = []
    for i in range(len(images)):
        texte_vision = transcrire_image(client, images[i])
        slide = {"numero": i + 1, "texte_ocr": textes[i], "texte_vision": texte_vision}
        slides.append(slide)
    return slides
