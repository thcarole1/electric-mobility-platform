
"""Fonctions génériques de sauvegarde et transfert de fichiers."""

import json
import logging
from datetime import datetime
from pathlib import Path
import polars as pl

from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


def generer_nom_fichier(identifiant: str, suffixe: str = "extract", extension: str = "json") -> str:
    """Génère un nom de fichier horodaté."""
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"{now}_{identifiant}_{suffixe}.{extension}"


def sauvegarder_local(donnees: dict, chemin: Path) -> None:
    """Sauvegarde les données JSON en local."""
    with open(chemin, "w") as f:
        json.dump(donnees, f)
    logger.info(f"Données JSON sauvegardées en local : {chemin}")


def uploader_s3(chemin_local: Path, bucket: str, cle_s3: str, client_s3) -> None:
    """Upload un fichier local vers S3."""
    try:
        client_s3.upload_file(str(chemin_local), bucket, cle_s3)
        logger.info(f"Upload réussi du fichier {chemin_local}")
    except NoCredentialsError:
        logger.error("Erreur : identifiants AWS manquants ou invalides.")
    except ClientError as e:
        logger.error(f"Erreur AWS lors de l'upload : {e}")

def sauvegarder_parquet_s3(df: pl.DataFrame, chemin_s3: str, storage_options: dict) -> None:
    """Sauvegarde un DataFrame Polars en Parquet directement sur S3."""
    df.write_parquet(chemin_s3, storage_options=storage_options)
    logger.info(f"Données sauvegardées en Parquet sur S3 : {chemin_s3}")
