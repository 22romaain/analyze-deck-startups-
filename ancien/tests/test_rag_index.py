"""Test de l'indexation et de la recherche (RAG) avec un faux embedding déterministe.

On n'appelle pas le vrai moteur ONNX (pas de téléchargement réseau en test) : on
injecte un embedding sac-de-mots pour valider la mécanique index -> recherche.
"""

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from src.rag.index import build_index, search


class FakeEmbedding(EmbeddingFunction):
    """Embedding déterministe et hors ligne : chaque mot incrémente une case d'un
    vecteur de taille fixe (sac de mots hashé). Suffit à tester la similarité."""

    DIM = 64

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        for text in input:
            vec = [0.0] * self.DIM
            for token in text.lower().split():
                vec[hash(token) % self.DIM] += 1.0
            vectors.append(vec)
        return vectors

    @staticmethod
    def name() -> str:
        return "fake"


def test_build_index_puis_search(tmp_path):
    courses = tmp_path / "courses"
    courses.mkdir()
    (courses / "doctrine.md").write_text(
        "# Burn multiple\n"
        "Le burn multiple mesure le capital brule par euro d ARR net nouveau.\n\n"
        "# Equipe\n"
        "Le founder market fit predit le succes au pre-seed.\n",
        encoding="utf-8",
    )
    ef = FakeEmbedding()
    db = tmp_path / "db"

    n = build_index(courses, chroma_dir=db, embedding_function=ef)
    assert n >= 2

    hits = search("capital brule par euro d ARR net", k=1, chroma_dir=db, embedding_function=ef)
    assert len(hits) == 1
    assert "burn multiple" in hits[0].text.lower()
    assert hits[0].source == "doctrine.md"
