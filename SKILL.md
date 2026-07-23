---
name: explication
description: Méthode d'explication de fin d'étape pour le projet Brawl Coach MCP. À utiliser systématiquement dès qu'une étape de développement est terminée, qu'un bug est corrigé, qu'une fonctionnalité est branchée, ou que l'utilisateur demande un bilan, un récap, un point d'avancement, ou « où on en est ». Structure le compte-rendu en trois blocs (langage normal, tableau des fonctions, état réel du chantier) et impose de ne jamais annoncer qu'une chose marche sans l'avoir exécutée. Déclencher même si l'utilisateur ne demande pas explicitement d'explication : après toute modification de code substantielle, c'est ce format qui s'applique.
---

# Explication de fin d'étape

Principe : expliquer pour apprendre, pas pour rendre compte. Le lecteur doit pouvoir relire son propre projet seul après avoir lu.

## Trois blocs, dans cet ordre

### 1. Ce que j'ai fait, en langage normal

Raconter sans vocabulaire technique, comme à quelqu'un qui ne code pas :

- **Le problème** : ce qui n'allait pas, décrit par ses conséquences concrètes, jamais par sa cause technique.
- **La correction** : ce qu'on a changé, et pourquoi ce choix plutôt qu'un autre.
- **Le résultat** : ce que ça donne à l'usage.
- **Les choix faits en son nom** : toute décision de présentation ou d'architecture prise sans consulter, avec sa raison. Le lecteur doit pouvoir la contester.

Interdits dans ce bloc : noms de fonctions, de classes, de librairies, de modules. Si un concept technique est indispensable, l'expliquer par une analogie, de préférence tirée du métier du lecteur.

### 2. Quelle fonction fait quoi

Un tableau. Une ligne par fonction touchée ou créée. Colonnes : la fonction, le fichier avec son numéro de ligne quand c'est utile, et ce qu'elle fait en une phrase de langage courant.

- Décrire l'intention, pas l'implémentation. « Remplit une fiche par dimension » plutôt que « itère sur les poids et instancie un modèle ».
- Mettre en gras la fonction qui sert de point d'entrée, s'il y en a une, et dire qu'elle est le seul appel dont le reste du code a besoin.
- Expliquer la convention du langage rencontrée en passant, une phrase maximum : le tiret bas devant un nom, un dictionnaire de traduction, un paramètre optionnel.
- Si un fichier se construit sur plusieurs étapes, redonner la liste complète de ses fonctions, pas seulement les nouvelles, pour qu'on voie l'ensemble.

### 3. Où on en est

- Ce qui est **branché et visible**, et ce qui **ne l'est pas encore**. Point capital : ne jamais laisser attendre un changement qui n'existe pas encore.
- L'état de ce qui tourne : serveur lancé ou arrêté, tests passants ou non, avec le compte exact.
- Ce qui reste dans le chantier en cours.
- Une question fermée pour la suite : « je lance X ? »

## Règles de vérification

- Ne jamais annoncer qu'une chose marche sans l'avoir exécutée. Si une branche du code n'a pas été parcourue pendant les vérifications, le dire.
- Donner les chiffres réels (nombre de tests, de lignes, avant et après), jamais d'approximation vague.
- Si une étape a été sautée ou un test a échoué, l'écrire noir sur blanc.

## Question de contrôle

Terminer par une question de contrôle seulement quand un concept nouveau a été introduit, et sur ce concept. Elle vise la compréhension du pourquoi, pas la récitation du quoi. Ne pas en poser à chaque message : une question rituelle n'apprend rien.
