"""Module d'ingestion : charge un PDF et rend chaque page en image PNG."""

from pathlib import Path

import fitz  # PyMuPDF — la librairie s'installe sous le nom pymupdf mais s'importe sous le nom fitz (héritage historique)


def load_deck(pdf_path: str) -> list[bytes]:
    """Ouvre un PDF et convertit chaque page en image PNG.

    Pourquoi des images plutôt que du texte ? Un pitch deck contient des graphiques,
    tableaux et mises en page que l'extraction texte perd totalement.
    Le modèle vision a besoin de "voir" la slide comme un analyste la verrait.

    Args:
        pdf_path: chemin vers le fichier PDF.

    Returns:
        Liste d'images PNG, une par page, sous forme de bytes.
    """
    path = Path(pdf_path)

    # Vérification explicite : mieux vaut une erreur claire qu'un traceback cryptique
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Le fichier doit être un PDF, reçu : {path.suffix}")

    doc = fitz.open(str(path))

    slides: list[bytes] = []
    for page in doc:
        # get_pixmap rend la page en image raster (comme une capture d'écran de la slide)
        # dpi=150 : bon compromis entre qualité pour le LLM et taille du fichier
        pixmap = page.get_pixmap(dpi=150)
        # tobytes("png") convertit le pixmap en bytes PNG prêts à être envoyés à l'API
        slides.append(pixmap.tobytes("png"))

    doc.close()

    return slides
