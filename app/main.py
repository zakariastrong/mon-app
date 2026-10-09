"""monapp : petite API FastAPI pour s'entraîner au déploiement canary."""

import os
import random

from fastapi import FastAPI, HTTPException

app = FastAPI(title="monapp")

ITEMS = [
    {"id": 1, "name": "clavier"},
    {"id": 2, "name": "souris"},
    {"id": 3, "name": "écran"},
]


def get_bug_rate() -> float:
    """Lit BUG_RATE à chaque appel (et non au démarrage).

    Avantage : les tests peuvent changer la variable avec monkeypatch.setenv
    sans recharger le module. Une valeur invalide vaut 0, et la valeur est
    bornée entre 0 et 1.
    """
    try:
        rate = float(os.getenv("BUG_RATE", "0"))
    except ValueError:
        return 0.0
    return min(max(rate, 0.0), 1.0)


@app.get("/health")
def health():
    # Toujours 200, même si /items est cassé : une probe /health
    # prouve que le processus répond, pas que l'appli fonctionne.
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": os.getenv("VERSION", "dev")}


@app.get("/items")
def items():
    # random.random() renvoie un nombre dans [0, 1[ :
    # avec BUG_RATE=0 on n'entre jamais ici, avec BUG_RATE=1 toujours.
    if random.random() < get_bug_rate():
        raise HTTPException(status_code=500, detail="bug simulé")
    return ITEMS
