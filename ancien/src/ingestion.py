"""Module d'ingestion : charge un PDF, convertit en markdown ou en images PNG."""

import io
from math import ceil
from pathlib import Path

import fitz  # PyMuPDF — la librairie s'installe sous le nom pymupdf mais s'importe sous le nom fitz (héritage historique)
from markitdown import MarkItDown
from PIL import Image


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

    # Vérification explicite
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


def group_slides(slides: list[bytes], max_images: int = 8) -> list[bytes]:
    """Regroupe les slides pour ne pas dépasser la limite d'images de l'API.

    Si le deck a 16 slides et la limite est 8, on empile les slides par 2
    verticalement : slide 1+2 deviennent une seule image, 3+4, etc.
    Le LLM voit toujours toutes les slides, juste regroupées.

    Analogie : c'est comme imprimer 2 slides par page pour réduire le nombre
    de pages envoyées, sans perdre d'information.
    """
    if len(slides) <= max_images:
        return slides

    # Combien de slides par groupe ? ceil(16/8) = 2, ceil(24/8) = 3
    group_size = ceil(len(slides) / max_images)

    grouped: list[bytes] = []
    for i in range(0, len(slides), group_size):
        batch = slides[i : i + group_size]

        # Ouvre chaque image du groupe avec Pillow
        images = [Image.open(io.BytesIO(b)) for b in batch]

        # Calcule la taille de l'image combinée (largeur max, hauteurs additionnées)
        total_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)

        # Crée une image vide blanche et colle chaque slide dedans
        combined = Image.new("RGB", (total_width, total_height), (255, 255, 255))
        y_offset = 0
        for img in images:
            combined.paste(img, (0, y_offset))
            y_offset += img.height

        # Convertit l'image combinée en bytes PNG
        buffer = io.BytesIO()
        combined.save(buffer, format="PNG")
        grouped.append(buffer.getvalue())

    return grouped


def convert_to_markdown(pdf_path: str) -> str | None:
    """Tente de convertir un PDF en markdown avec markitdown.

    Retourne le texte markdown si la qualité est suffisante,
    None si le résultat est inutilisable (polices custom, texte vide).
    """
    try:
        md = MarkItDown()
        result = md.convert(pdf_path)
        text = result.text_content
    except Exception:
        return None

    # Vérification qualité : trop de caractères encodés = PDF mal parsé
    if not text or len(text.strip()) < 50:
        return None
    # Ratio de "(cid:" dans le texte — seuil à 5% = inutilisable
    cid_count = text.count("(cid:")
    if cid_count > len(text) * 0.05:
        return None

    return text.strip()
