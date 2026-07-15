"""Module RAG : indexation locale des cours VC et récupération de passages.

Chaîne : lecture des documents -> découpage en passages -> embeddings locaux
(ONNX via ChromaDB) -> stockage vectoriel -> récupération par similarité.
Aucun appel API : tout est local.
"""
