Roadmap jusqu'à la fin de l'extraction

1. lecture.py : OCR optionnel, le programme continue en vision seule si l'OCR échoue
   - appel OCR sans relance (retries=RetryConfig("none", ...)) dans un try / except SDKError
   - deux consignes vision : CONSIGNE_COMPLEMENT (OCR ok) et CONSIGNE_COMPLETE (OCR indisponible, tout transcrire)
   - transcrire_image reçoit la consigne en paramètre, texte_ocr = "[OCR indisponible]" en cas d'échec
2. remplissage.py : ajouter à la consigne "si l'OCR est indisponible, la vision fait foi pour tout"
3. quota OCR : le propriétaire de la clé vérifie Admin Panel › API › Limits (console.mistral.ai), sinon demande au support Mistral
4. test à lancer sur 2-3 vrais decks de secteurs différents (cf. decks en local)
5. fiche.py : décider d'ajouter slide dans Chiffre (citer la source dans le mémo)
6. si le débit bloque : sauter l'appel vision sur les slides sans visuel (page.get_images() / page.get_drawings()), tester dpi 100-120
7. si la qualité est mauvaise : découper le remplissage en 3-4 groupes de sections
