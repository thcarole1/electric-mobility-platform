"""Enchaîne l'ingestion, le nettoyage, le chargement DuckDB, la météo
et la génération de sessions, en local, du début à la fin."""

import logging
import os
from datetime import date
from pathlib import Path
import argparse

import boto3
import duckdb
import polars as pl
from validation.schema import valider_schema
from dotenv import load_dotenv

from ingestion.openchargemap import ingerer_openchargemap
from ingestion.meteo import ingerer_meteo
from cleaning.openchargemap import nettoyer_openchargemap
from cleaning.meteo import assembler_meteo_multi_poi
from warehouse.duckdb_loader import (
    charger_openchargemap_dans_duckdb,
    charger_meteo_dans_duckdb,
    charger_sessions_dans_duckdb,
)
from simulation.sessions import generer_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_PATH = Path(__file__).resolve().parent
BUCKET_S3 = "electric-mobility-platform-thierry"
NB_SESSIONS = 455
DATE_DEBUT_METEO = date(2026, 7, 20)
DATE_FIN_METEO = date(2026, 7, 24)


def main(chemin_db: str):
    load_dotenv(dotenv_path=ROOT_PATH / ".env")
    cle_api = os.environ.get("OCM_API_KEY")
    client_s3 = boto3.client("s3")

    # 1. Ingestion Open Charge Map (nouvel appel API, pas de réutilisation d'un ancien fichier)
    nom_fichier = ingerer_openchargemap(
        latitude=48.856614,
        longitude=2.352222,
        distance=5,
        ville="paris",
        cle_api=cle_api,
        bucket_s3=BUCKET_S3,
        client_s3=client_s3,
        root_path=ROOT_PATH,
    )
    if nom_fichier is None:
        logger.error("Pipeline interrompu : échec de l'ingestion Open Charge Map.")
        return

    chemin_json = ROOT_PATH / "data" / "raw" / nom_fichier
    with open(chemin_json, "r") as f:
        import json
        donnees_json = json.load(f)

    # 2. Nettoyage
    poi_df, connections_df = nettoyer_openchargemap(donnees_json)

    # 3. Chargement poi/connections dans DuckDB
    con = duckdb.connect(chemin_db)
    charger_openchargemap_dans_duckdb(con, poi_df, connections_df)

    # 4. Ingestion météo, un appel par POI
    correspondance_poi_fichier = {}
    for row in poi_df.iter_rows(named=True):
        nom_fichier_meteo = ingerer_meteo(
            latitude=row["latitude"],
            longitude=row["longitude"],
            start_date=DATE_DEBUT_METEO.isoformat(),
            end_date=DATE_FIN_METEO.isoformat(),
            hourly="temperature_2m",
            identifiant=f"poi{row['poi_id']}",
            bucket_s3=BUCKET_S3,
            client_s3=client_s3,
            root_path=ROOT_PATH,
        )
        if nom_fichier_meteo is not None:
            correspondance_poi_fichier[row["poi_id"]] = nom_fichier_meteo

    # 5. Assemblage et chargement météo
    meteo_globale = assembler_meteo_multi_poi(correspondance_poi_fichier, ROOT_PATH)
    meteo_df = pl.DataFrame(meteo_globale)
    valider_schema(
        meteo_df,
        {"poi_id": pl.Int64, "time": pl.String, "temperature_2m": pl.Float64},
        "meteo",
    )
    charger_meteo_dans_duckdb(con, meteo_df)

    # 6. Génération et chargement des sessions
    connections_operationnelles = connections_df.filter(pl.col("is_operational"))
    sessions = [
        generer_session(con, connections_operationnelles, DATE_DEBUT_METEO, DATE_FIN_METEO)
        for _ in range(NB_SESSIONS)
    ]
    sessions_df = pl.DataFrame(sessions)
    charger_sessions_dans_duckdb(con, sessions_df)

    con.close()
    logger.info("Pipeline terminé avec succès.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exécute le pipeline complet en local.")
    parser.add_argument(
        "--db",
        default=str(ROOT_PATH / "data" / "warehouse" / "electric_mobility.duckdb"),
        help="Chemin vers la base DuckDB cible (par défaut : la base de production).",
    )
    args = parser.parse_args()
    main(args.db)
