from pydantic import BaseModel, Field


class Equipe(BaseModel):
    ...


class Marche(BaseModel):
    ...


class Traction(BaseModel):
    ...

class Finance(BaseModel):
    ...


class Produit(BaseModel):
    ...


class Levee(BaseModel):
    ...


class Fiche(BaseModel):
    societe : str | None
    equipe : Equipe | None
    marche : Marche | None
    traction : Traction | None
    finance : Finance | None
    produit : Produit | None
    levee : Levee | None
    contradictions : list[str]
