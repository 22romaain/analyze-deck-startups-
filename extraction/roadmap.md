

Roadmap jusqu'à la fin de l'extraction

2. lecture.py : sauter l'appel vision sur les slides sans visuel (page.get_images() / page.get_drawings())
3. lecture.py : débloquer l'OCR (limite de taille, upload du PDF via client.files + URL signée), tester dpi 100-120
4. extraire.py : relance automatique sur erreur 429 (retry_config du client Mistral)
5. remplissage.py : consigne générale (ne rien inventer, None si absent, garder unités et périodes, signaler les contradictions OCR vs vision)
6. remplissage.py : un appel chat.parse par section, puis assemblage de la fiche
7. remplissage.py : routage, Identite remplie en premier puis uniquement les modules correspondant à types_business_model pour les conditions spécifiques
8. trancher où remplir contradictions (par section puis regroupées dans la Fiche)
9. paralléliser les appels vision (par slide) et les appels de section (après Identite)
10. test à lancer (cf. decks en local)
