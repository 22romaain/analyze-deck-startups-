##Update##
#La pipeline d'extraction du texte et des données d'un pitch deck est complète : PDF -> lecture -> fiche complète avec data structurée#

##Ce qu'il reste à faire##
- ajouter la consigne de remplissage.py pour le client Mistral
- débloquer l'OCR/voir la limite de requête et d'images envoyées
- remplir les critères de fiche.py (pour savoir ce qu'on doit récupérer)
- option à trancher : supprimer transcrire_image et envoyer les images + l'OCR directement à remplir_fiche (2 appels LLM au lieu de N+2)