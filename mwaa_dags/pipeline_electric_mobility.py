"""DAG Airflow — pipeline d'ingestion et de nettoyage Electric Mobility Platform.

Ingère Open Charge Map, nettoie et sauvegarde poi/connections sur S3,
puis (en parallèle) ingère la météo pour chaque POI, l'assemble et la
sauvegarde sur S3.

Le chargement DuckDB et la génération des sessions restent des étapes
locales, exécutées séparément (voir run_pipeline.py) — ce DAG s'arrête
à la production des fichiers Parquet nettoyés sur S3 (voir ADR-021).
"""

import json
import os
from datetime import datetime
from pathlib import Path

import boto3
import polars as pl
from airflow import DAG
from airflow.operators.python import PythonOperator

from ingestion.openchargemap import ingerer_openchargemap
from ingestion.meteo import ingerer_meteo
from cleaning.openchargemap import nettoyer_openchargemap
from cleaning.meteo import assembler_meteo_multi_poi
from emp_common.storage import sauvegarder_parquet_s3

BUCKET_S3 = "electric-mobility-platform-thierry"
DATE_DEBUT_METEO = "2026-07-20"
DATE_FIN_METEO = "2026-07-24"


def _storage_options() -> dict:
    return {
        "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "aws_region": "eu-west-3",
    }


def tache_ingestion_openchargemap(**context):
    cle_api = os.environ.get("AIRFLOW__ENV__OCM_API_KEY")
    client_s3 = boto3.client("s3")

    root_path = Path("/tmp")
    (root_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    nom_fichier = ingerer_openchargemap(
        latitude=48.856614,
        longitude=2.352222,
        distance=5,
        ville="paris",
        cle_api=cle_api,
        bucket_s3=BUCKET_S3,
        client_s3=client_s3,
        root_path=Path("/tmp"),
    )
    return nom_fichier


def tache_nettoyage_openchargemap(**context):
    ti = context["ti"]
    nom_fichier = ti.xcom_pull(task_ids="ingestion_openchargemap")

    client_s3 = boto3.client("s3")
    chemin_local = Path("/tmp") / nom_fichier
    client_s3.download_file(BUCKET_S3, f"raw/{nom_fichier}", str(chemin_local))

    with open(chemin_local, "r") as f:
        donnees_json = json.load(f)

    poi_df, connections_df = nettoyer_openchargemap(donnees_json)

    storage_options = _storage_options()
    chemin_poi_s3 = f"s3://{BUCKET_S3}/processed/poi/poi.parquet"
    chemin_connections_s3 = f"s3://{BUCKET_S3}/processed/connections/connections.parquet"

    sauvegarder_parquet_s3(poi_df, chemin_poi_s3, storage_options)
    sauvegarder_parquet_s3(connections_df, chemin_connections_s3, storage_options)

    return {"poi": chemin_poi_s3, "connections": chemin_connections_s3}


def tache_ingestion_meteo(**context):
    ti = context["ti"]
    chemins = ti.xcom_pull(task_ids="nettoyage_openchargemap")

    storage_options = _storage_options()
    poi_df = pl.read_parquet(chemins["poi"], storage_options=storage_options)

    client_s3 = boto3.client("s3")
    correspondance_poi_fichier = {}

    for row in poi_df.iter_rows(named=True):
        nom_fichier_meteo = ingerer_meteo(
            latitude=row["latitude"],
            longitude=row["longitude"],
            start_date=DATE_DEBUT_METEO,
            end_date=DATE_FIN_METEO,
            hourly="temperature_2m",
            identifiant=f"poi{row['poi_id']}",
            bucket_s3=BUCKET_S3,
            client_s3=client_s3,
            root_path=Path("/tmp"),
        )
        if nom_fichier_meteo is not None:
            correspondance_poi_fichier[row["poi_id"]] = nom_fichier_meteo

    return correspondance_poi_fichier


def tache_assemblage_meteo(**context):
    ti = context["ti"]
    correspondance_poi_fichier = ti.xcom_pull(task_ids="ingestion_meteo")

    client_s3 = boto3.client("s3")
    root_path = Path("/tmp")
    (root_path / "data" / "raw").mkdir(parents=True, exist_ok=True)

    for poi_id, nom_fichier in correspondance_poi_fichier.items():
        client_s3.download_file(
            BUCKET_S3,
            f"raw/{nom_fichier}",
            str(root_path / "data" / "raw" / nom_fichier),
        )

    meteo_globale = assembler_meteo_multi_poi(correspondance_poi_fichier, root_path)
    meteo_df = pl.DataFrame(meteo_globale)

    storage_options = _storage_options()
    chemin_meteo_s3 = f"s3://{BUCKET_S3}/processed/meteo/meteo.parquet"
    sauvegarder_parquet_s3(meteo_df, chemin_meteo_s3, storage_options)

    return chemin_meteo_s3


with DAG(
    dag_id="electric_mobility_pipeline",
    start_date=datetime(2026, 8, 17),
    schedule=None,
    catchup=False,
) as dag:

    ingestion_openchargemap = PythonOperator(
        task_id="ingestion_openchargemap",
        python_callable=tache_ingestion_openchargemap,
    )

    nettoyage_openchargemap = PythonOperator(
        task_id="nettoyage_openchargemap",
        python_callable=tache_nettoyage_openchargemap,
    )

    ingestion_meteo = PythonOperator(
        task_id="ingestion_meteo",
        python_callable=tache_ingestion_meteo,
    )

    assemblage_meteo = PythonOperator(
        task_id="assemblage_meteo",
        python_callable=tache_assemblage_meteo,
    )

    ingestion_openchargemap >> nettoyage_openchargemap >> ingestion_meteo >> assemblage_meteo
