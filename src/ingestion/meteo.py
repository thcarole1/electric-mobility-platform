"""Ingestion des données météo depuis Open-Meteo (Historical Weather API)."""

import logging
import time

import requests

from common.io import generer_nom_fichier, sauvegarder_local, uploader_s3

logger = logging.getLogger(__name__)

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
USER_AGENT = "electric-mobility-platform/0.1 (projet portfolio Data Engineering)"
MAX_TENTATIVES = 3
DELAI_ENTRE_TENTATIVES = 5

def appeler_api_meteo(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    hourly: str,
) -> dict | None:
    """Appelle l'API Historical Weather d'Open-Meteo et renvoie les résultats, ou None en cas d'échec."""

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": hourly,
    }

    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}

    for tentative in range(1, MAX_TENTATIVES + 1):
        response = requests.get(BASE_URL, headers=headers, params=params)

        if response.status_code == 200:
            logger.info("Requête Open-Meteo effectuée avec succès.")
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

def ingerer_meteo(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    hourly: str,
    identifiant: str,
    bucket_s3: str,
    client_s3,
    root_path,
) -> None:
    """Orchestre l'ingestion complète : appel API, sauvegarde locale, upload S3."""

    # Appeler generer_nom_fichier(ville)
    nom_fichier = generer_nom_fichier(identifiant, suffixe="meteo")

    # Construire le chemin local complet
    chemin_local = root_path / "data" / "raw" / nom_fichier

    # Appeler appeler_api_meteo(...)
    donnees = appeler_api_meteo(
                                    latitude,
                                    longitude,
                                    start_date,
                                    end_date,
                                    hourly,
                                )
    if donnees is None:
        logger.error("Ingestion interrompue : échec de l'appel API.")
        return

    # Appeler sauvegarder_local(...)
    sauvegarder_local(donnees, chemin_local)

    # Construire la clé S3 (f"raw/{nom_fichier}")
    cle_s3 = "raw/" + nom_fichier

    # Appeler uploader_s3(...)
    uploader_s3(chemin_local, bucket_s3, cle_s3, client_s3)
