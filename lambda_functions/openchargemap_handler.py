import json
import logging
import os
from pathlib import Path

import boto3

from ingestion.openchargemap import ingerer_openchargemap

logging.getLogger().setLevel(logging.INFO)


def lambda_handler(event, context):
    """Point d'entrée Lambda pour l'ingestion Open Charge Map."""
    cle_api = os.environ.get("OCM_API_KEY")
    client_s3 = boto3.client("s3")

    root_path = Path("/tmp")
    (root_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    nom_fichier = ingerer_openchargemap(
        latitude=48.856614,
        longitude=2.352222,
        distance=5,
        ville="paris",
        cle_api=cle_api,
        bucket_s3="electric-mobility-platform-thierry",
        client_s3=client_s3,
        root_path=root_path,
    )

    return {
        "statusCode": 200 if nom_fichier else 500,
        "body": json.dumps({"fichier": nom_fichier}),
    }
