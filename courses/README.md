# Corpus RAG : tes supports de cours VC

Dépose ici tes supports de cours (fichiers `.pdf`, `.md`, `.txt`). Le script
d'indexation lit **tout** le dossier, découpe chaque document en passages, les
transforme en vecteurs (embeddings locaux) et les range dans la base ChromaDB.

## Utilisation

1. Copie tes fichiers de cours dans ce dossier.
2. Relance l'indexation (voir la commande dans le README racine / CLAUDE.md).
3. Interroge le corpus : le RAG retrouve les passages les plus proches d'une requête.

## Notes

- Le contenu de ce dossier n'est **pas** versionné par git (cours personnels).
  Seul ce README l'est.
- Rien ne quitte ta machine : embeddings et base vectorielle sont 100% locaux.
- Au démarrage, le référentiel `criteria/criteres_analyse_vc.md` sert de corpus
  d'amorçage pour valider la chaîne de bout en bout.
