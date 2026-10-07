Roadmap de l'analyse

1. analyse.py : vue d'ensemble des priorités
   - Analyse reçoit un champ priorites: list[str]
   - consigne : "priorites : les 5 points à examiner en premier, toutes dimensions confondues, du plus important au moins important"
   - reste neutre : dit quoi regarder en premier, jamais s'il faut investir

2. fiche.py : garder la slide source des chiffres (correctif côté extraction)
   - Chiffre reçoit un champ slide: int | None = champ("numéro de la slide d'où vient le chiffre")
   - analyse.py : consigne "cite la slide source quand la fiche la donne"
