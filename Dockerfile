# Image de base : version précise, jamais "latest"
FROM python:3.12.15-slim

# Version de l'appli, fournie au build : --build-arg VERSION=1.0.0
ARG VERSION=dev
ENV VERSION=${VERSION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances d'abord : cette couche reste en cache tant que
# requirements.txt ne change pas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Utilisateur non-root avec un uid fixe
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser

# Un NUMÉRO et pas un nom : Kubernetes (runAsNonRoot) peut ainsi
# vérifier que l'uid n'est pas 0
USER 10001

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
