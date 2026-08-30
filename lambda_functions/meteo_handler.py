import json
import logging
import os
from datetime import date
from pathlib import Path

import boto3

from ingestion.meteo import ingerer_meteo

logging.getLogger().setLevel(logging.INFO)


def lambda_handler(event, context):
    """Point d'entrée Lambda pour l'ingestion météo (un seul POI fixe)."""
    client_s3 = boto3.client("s3")

    root_path = Path("/tmp")
    (root_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    aujourd_hui = date.today().strftime("%Y-%m-%d")

    nom_fichier = ingerer_meteo(
        latitude=48.856614,
        longitude=2.352222,
        start_date=aujourd_hui,
        end_date=aujourd_hui,
        hourly="temperature_2m",
        identifiant="7008",
        bucket_s3="electric-mobility-platform-thierry",
        client_s3=client_s3,
        root_path=root_path,
    )

    return {
        "statusCode": 200 if nom_fichier else 500,
        "body": json.dumps({"fichier": nom_fichier}),
    }
