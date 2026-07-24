"""Docstring du module — une ligne qui explique son rôle."""

# 1. Imports (standard library, puis tiers, puis internes au projet)
import os
import time
import json
from pathlib import Path
from datetime import datetime

import requests
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

# 2. Constantes du module
ROOT_PATH = Path.cwd().resolve().parent
BASE_URL = "https://api.openchargemap.io/v3/poi"
USER_AGENT = "electric-mobility-platform/0.1 (projet portfolio Data Engineering)"
MAX_TENTATIVES = 3
DELAI_ENTRE_TENTATIVES = 5  # secondes

# 3. Fonctions (des plus "basses" / techniques vers les plus "hautes" / orchestratrices)
def generer_nom_fichier(ville: str) -> str:
    """Génère un nom de fichier horodaté pour une extraction."""
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{now}_{ville}_extract.json"

def appeler_api_openchargemap(latitude: float, longitude: float, distance: int, cle_api: str) -> dict | None:
    """Appelle l'API Open Charge Map et renvoie les résultats, ou None en cas d'échec."""

    querystring = {
        "output": "json",
        "key": cle_api,
        "latitude": latitude,
        "longitude": longitude,
        "distance": distance,
        "distanceunit": "km",
        "maxresults": 50
    }
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}

    for tentative in range(1, MAX_TENTATIVES + 1):
        response = requests.get(BASE_URL, headers=headers, params=querystring)

        if response.status_code == 200:
            logger.info("Requête openchargemap effectuée avec succès.")
            return response.json()

        # ta condition ici (5xx ou 429)
        if  response.status_code == 429 or 500 <= response.status_code < 600:
            logger.warning(f"Tentative {tentative}/{MAX_TENTATIVES} échouée (code {response.status_code}). Nouvel essai dans {DELAI_ENTRE_TENTATIVES}s.")
            time.sleep(DELAI_ENTRE_TENTATIVES)

        else:
            # erreur non temporaire, ne sert à rien de réessayer
            logger.error(f"Échec de la requête, code {response.status_code}, détail {response.text}")
            return None

    logger.error(f"Échec après {MAX_TENTATIVES} tentatives.")
    return None

def sauvegarder_local(donnees: dict, chemin: Path) -> None:
    """Sauvegarde les données JSON en local."""
    with open(chemin, "w") as f:
        json.dump(donnees, f)
    logger.info(f"Données JSON sauvegardées en local : {chemin}")

def uploader_s3(chemin_local: Path, bucket: str, cle_s3: str, client_s3) -> None:
    """Upload un fichier local vers S3."""
    try:
        client_s3.upload_file(str(chemin_local), bucket, cle_s3)
        logger.info(f"Upload S3 réussi du fichier {chemin_local}")
    except NoCredentialsError:
        logger.error("Erreur : identifiants AWS manquants ou invalides.")
    except ClientError as e:
        logger.error(f"Erreur AWS lors de l'upload : {e}")

# 4. Fonction d'orchestration, qui assemble les précédentes
def ingerer_openchargemap(
    latitude: float,
    longitude: float,
    distance: int,
    ville: str,
    cle_api: str,
    bucket_s3: str,
    client_s3,
    root_path: Path,
) -> None:
    """Orchestre l'ingestion complète : appel API, sauvegarde locale, upload S3."""

    # Appeler generer_nom_fichier(ville)
    nom_fichier = generer_nom_fichier(ville)

    # Construire le chemin local complet
    chemin_local = root_path / "data" / "raw" / nom_fichier

    # Appeler appeler_api_openchargemap(...)
    donnees = appeler_api_openchargemap(latitude, longitude, distance, cle_api)
    if donnees is None:
        logger.error("Ingestion interrompue : échec de l'appel API.")
        return

    # Appeler sauvegarder_local(...)
    sauvegarder_local(donnees, chemin_local)

    # Construire la clé S3 (f"raw/{nom_fichier}")
    cle_s3 = "raw/" + nom_fichier

    # Appeler uploader_s3(...)
    uploader_s3(chemin_local, bucket_s3, cle_s3, client_s3)
