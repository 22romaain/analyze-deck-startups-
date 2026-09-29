"""Indexation et récupération vectorielle via ChromaDB (embeddings locaux).

build_index reconstruit la base à partir du dossier corpus ; search retourne les
passages les plus proches d'une requête. L'embedding_function est injectable :
None -> moteur ONNX par défaut de ChromaDB (local) ; en test, un faux embedding
déterministe permet de tourner hors ligne.
"""

from pathlib import Path

import chromadb
from pydantic import BaseModel

from src.rag.documents import build_chunks

# Base vectorielle persistante à la racine (régénérable, ignorée par git).
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"
COLLECTION_NAME = "courses"


class SearchHit(BaseModel):
    """Un passage retrouvé : son texte, sa source, sa section, sa distance à la requête.

    distance : plus elle est petite, plus le passage est proche de la requête.
    """
    text: str
    source: str
    section: str
    distance: float


def _collection(client: "chromadb.ClientAPI", embedding_function):
    """Récupère (ou crée) la collection. On ne passe embedding_function que si fournie,
    sinon ChromaDB applique son moteur par défaut (ONNX MiniLM)."""
    kwargs = {"embedding_function": embedding_function} if embedding_function is not None else {}
    return client.get_or_create_collection(COLLECTION_NAME, **kwargs)


def build_index(
    courses_dir: str | Path, chroma_dir: str | Path | None = None, embedding_function=None
) -> int:
    """Reconstruit l'index depuis zéro et retourne le nombre de passages indexés.

    Reconstruction complète (delete puis recreate) : idempotent, pas de doublons
    quand on relance après avoir ajouté des cours.
    """
    client = chromadb.PersistentClient(path=str(chroma_dir or CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # la collection n'existait pas encore

    collection = _collection(client, embedding_function)
    chunks = build_chunks(courses_dir)
    if chunks:
        collection.add(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{"source": c.source, "section": c.section} for c in chunks],
        )
    return len(chunks)


def search(
    query: str, k: int = 5, chroma_dir: str | Path | None = None, embedding_function=None
) -> list[SearchHit]:
    """Retourne les k passages les plus proches de la requête (par similarité)."""
    client = chromadb.PersistentClient(path=str(chroma_dir or CHROMA_DIR))
    collection = _collection(client, embedding_function)
    res = collection.query(query_texts=[query], n_results=k)

    documents = res["documents"][0]
    metadatas = res["metadatas"][0]
    distances = res["distances"][0]
    return [
        SearchHit(
            text=text, source=meta.get("source", ""),
            section=meta.get("section", ""), distance=dist,
        )
        for text, meta, dist in zip(documents, metadatas, distances)
    ]
