"""Lecture des documents de cours et découpage en passages (chunks).

Pur et déterministe : aucun embedding, aucune API. On lit les fichiers du dossier
corpus et on les fractionne en passages courts, chacun rattaché à sa section.
Analogie : préparer la data room en fiches thématiques avant de l'indexer.
"""

from pathlib import Path

import fitz  # PyMuPDF, déjà utilisé par l'ingestion
from pydantic import BaseModel

# Taille cible d'un passage, en caractères. Assez court pour être précis à la
# récupération, assez long pour garder du contexte. Réglable si besoin.
CHUNK_MAX_CHARS = 800

# Extensions de cours supportées. Le README du dossier n'est jamais indexé.
SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


class Chunk(BaseModel):
    """Un passage indexable : son texte, sa source (fichier) et sa section."""
    id: str
    text: str
    source: str
    section: str = ""


def _read_pdf(path: Path) -> str:
    """Extrait le texte brut d'un PDF (déterministe, hors ligne)."""
    doc = fitz.open(str(path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def _read_file(path: Path) -> str:
    """Lit un fichier de cours en texte, selon son extension."""
    if path.suffix.lower() == ".pdf":
        return _read_pdf(path)
    return path.read_text(encoding="utf-8")


def read_documents(courses_dir: str | Path) -> list[tuple[str, str]]:
    """Retourne (nom_fichier, texte) pour chaque cours du dossier, README exclu."""
    directory = Path(courses_dir)
    documents: list[tuple[str, str]] = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in SUPPORTED_SUFFIXES or path.name == "README.md":
            continue
        text = _read_file(path)
        if text.strip():
            documents.append((path.name, text))
    return documents


def chunk_text(text: str, source: str) -> list[Chunk]:
    """Découpe un document en passages d'environ CHUNK_MAX_CHARS, par section.

    Une ligne de titre markdown ('#', '##', ...) ouvre une nouvelle section et
    ferme le passage courant. Les lignes vides sont des frontières souples : on
    coupe seulement si le passage a atteint la taille cible.
    """
    section = ""
    buffer: list[str] = []
    collected: list[tuple[str, str]] = []

    def buffer_len() -> int:
        return sum(len(line) for line in buffer)

    def flush() -> None:
        content = "\n".join(buffer).strip()
        buffer.clear()
        if content:
            collected.append((section, content))

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            flush()
            section = line.lstrip("#").strip()
            continue
        if not line.strip():
            if buffer_len() >= CHUNK_MAX_CHARS:
                flush()
            continue
        buffer.append(line)
        if buffer_len() >= CHUNK_MAX_CHARS:
            flush()
    flush()

    return [
        Chunk(id=f"{source}::{i}", text=content, source=source, section=sec)
        for i, (sec, content) in enumerate(collected)
    ]


def build_chunks(courses_dir: str | Path) -> list[Chunk]:
    """Lit tout le dossier corpus et retourne la liste complète des passages."""
    chunks: list[Chunk] = []
    for source, text in read_documents(courses_dir):
        chunks += chunk_text(text, source)
    return chunks
