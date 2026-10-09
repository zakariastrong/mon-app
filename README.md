# monapp

Petite API FastAPI qui servira à tester un déploiement canary sur Kubernetes
(Argo Rollouts + analyse k6).

## Routes

| Route          | Réponse                                                  |
|----------------|----------------------------------------------------------|
| `GET /health`  | `{"status": "ok"}`, **toujours 200**                     |
| `GET /version` | `{"version": "<VERSION>"}` (`dev` par défaut)            |
| `GET /items`   | liste d'éléments, ou 500 « bug simulé » selon `BUG_RATE` |

> `/health` renvoie 200 même si `/items` est cassé : c'est voulu. Une probe
> `/health` prouve que le processus répond, pas que l'application fonctionne.

## Variables d'environnement

| Variable   | Défaut | Rôle                                                       |
|------------|--------|------------------------------------------------------------|
| `VERSION`  | `dev`  | version renvoyée par `/version`                            |
| `BUG_RATE` | `0`    | probabilité (0 à 1) qu'un appel à `/items` renvoie une 500 |

Les deux variables sont lues **à chaque requête**.

## Lancer en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Puis : `curl http://localhost:8000/health`

## Lancer les tests

```bash
python -m pytest -v
```

On utilise `python -m pytest` (et pas `pytest` tout court) : cela ajoute le
dossier courant au chemin Python, donc `from app.main import app` fonctionne.

## Construire et lancer l'image Docker

```bash
docker build --build-arg VERSION=1.0.0 -t monapp:1.0.0 .

# Vérifier l'utilisateur non-root (doit afficher uid=10001)
docker run --rm --entrypoint id monapp:1.0.0

# Lancer l'API
docker run --rm -p 8000:8000 monapp:1.0.0

# Simuler une mauvaise version (~30 % d'erreurs sur /items)
docker run --rm -p 8000:8000 -e BUG_RATE=0.3 monapp:1.0.0
```

Les logs d'accès d'uvicorn sont activés : chaque requête apparaît
(`"GET /items HTTP/1.1" 200`), ce qui permet de compter les appels reçus par
un conteneur avec `docker logs <conteneur> | grep -c "GET /items"`.

## Intégration continue

Le fichier `.github/workflows/ci.yml` définit deux jobs GitHub Actions.

### Job `tests` : à chaque pull request vers `main` et à chaque tag `v*`

1. Installe Python 3.12 et les dépendances.
2. Lance `python -m pytest` : si un test échoue, la PR est bloquée.
3. Lance **Bandit** (`bandit -r app/ -ll`), un outil de SAST (analyse statique de
   sécurité du code) : il échoue s'il trouve un problème de gravité moyenne ou haute.

### Job `image` : seulement sur un tag `v*`, et seulement si `tests` a réussi

1. Calcule la version depuis le tag : `v1.0.0` → `1.0.0`.
2. Se connecte à `ghcr.io` avec le `GITHUB_TOKEN` fourni automatiquement par GitHub.
3. Construit l'image avec `--build-arg VERSION=<version>`.
4. Scanne l'image avec **Trivy** *avant* de la publier : s'il trouve une faille
   HIGH ou CRITICAL qui a déjà un correctif, le job échoue et l'image n'est pas poussée.
5. Pousse `ghcr.io/<owner en minuscules>/monapp:<version>`. Jamais de tag `latest` :
   une version publiée est immuable et on sait toujours ce qui tourne.

### Publier une nouvelle version

```bash
git tag v1.0.0
git push origin v1.0.0
```
