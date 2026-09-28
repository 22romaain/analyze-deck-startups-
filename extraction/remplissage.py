from extraction.fiche import Fiche

CONSIGNE = """"""


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
    reponse = client.chat.parse(model="ministral-8b-latest", messages=messages, response_format=Fiche)
    return reponse.choices[0].message.parsed
