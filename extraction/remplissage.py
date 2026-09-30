from extraction.fiche import Fiche

CONSIGNE = """Tu es analyste VC. Tu reçois un pitch deck, slide par slide. Pour chaque slide :
- "OCR" : le texte exact de la slide. Il fait foi pour le texte et les chiffres écrits.
- "Vision" : ce que l'OCR ne capte pas (graphiques, tableaux, logos, éléments cochés ou surlignés).

Ta mission : remplir la fiche de la façon la plus complète et la plus fidèle possible.

Remplir
- Parcours tout le deck et remplis chaque champ dès qu'une information y correspond, même si le deck la formule autrement (ex : "revenus", "CA" et "ventes" désignent le chiffre d'affaires).
- Une information peut se trouver sur n'importe quelle slide : ne te limite pas à la slide qui porte le titre du sujet.
- Range chaque information dans le champ le plus précis, sans la répéter ailleurs.
- Remplis un module optionnel (data, tech, arr, retention, marketplace, aarrr) seulement si le deck contient des informations qui lui correspondent. Sinon, laisse-le à null.

Ne rien inventer
- Si le deck ne dit rien sur un champ, laisse-le à null. Une absence n'est ni un zéro ni un "non".
- Ne calcule rien et ne déduis rien : pas de ratio, pas de total, pas d'ARR à partir du MRR, sauf si le deck donne lui-même le chiffre.
- Booléens : true si le deck le montre, false seulement s'il dit explicitement le contraire, null sinon.
- Listes de valeurs imposées : utilise uniquement les valeurs autorisées.

Chiffres
- valeur : le nombre développé (1,2M → 1200000 ; 15% → 15).
- unite : la devise ou l'unité telle qu'affichée (€, $, %, clients, mois).
- periode : l'année, le mois ou la fréquence (2024, mars 2025, MoM, par an).
- Une série (par année, par mois) donne un élément par point.
- Un chiffre projeté ou prévisionnel va uniquement dans previsionnel, jamais dans traction, cash ou arr.

Textes
- Courts et factuels, en français, en reprenant les termes et les chiffres du deck.
- Ce que la société affirme reste une affirmation : écris "revendique", "selon la société".

Contradictions
- Ajoute une entrée dès que deux informations du deck se contredisent (entre deux slides, ou entre l'OCR et la vision), sous la forme :
  "sujet : valeur A (slide X) vs valeur B (slide Y)"."""


def remplir_fiche(client, slides):
    blocs = []
    for slide in slides:
        bloc = f"## Slide {slide['numero']}\n### OCR\n{slide['texte_ocr']}\n### Vision\n{slide['texte_vision']}"
        blocs.append(bloc)
    texte = "\n\n".join(blocs)
    messages = [
        {"role": "system", "content": CONSIGNE},
        {"role": "user", "content": texte},
    ]
    reponse = client.chat.parse(model="mistral-medium-latest", messages=messages, response_format=Fiche)
    return reponse.choices[0].message.parsed
