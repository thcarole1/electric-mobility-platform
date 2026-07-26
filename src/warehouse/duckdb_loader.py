
"""Chargement des données Open Charge Map dans DuckDB."""

import logging

import polars as pl
from duckdb import DuckDBPyConnection

logger = logging.getLogger(__name__)


def creer_table_poi(con: DuckDBPyConnection) -> None:
    """Crée la table poi si elle n'existe pas déjà."""

    con.execute("""
    CREATE TABLE IF NOT EXISTS poi (
        poi_id BIGINT PRIMARY KEY,
        title VARCHAR,
        town VARCHAR,
        town_normalisee VARCHAR,
        postcode VARCHAR,
        latitude DOUBLE,
        longitude DOUBLE,
        number_of_points BIGINT,
        usage_cost VARCHAR,
        date_last_confirmed VARCHAR
        )
    """)

    # Attention : Message à adapter pour bien faire comprendre le cas où la table existe déjà.
    logger.info("Table POI créée avec succès.")


def inserer_poi(con: DuckDBPyConnection, poi_df: pl.DataFrame) -> None:
    """Insère ou met à jour les données poi (upsert sur poi_id)."""

    con.execute("""
    INSERT INTO poi (poi_id, title, town, town_normalisee, postcode, latitude, longitude, number_of_points, usage_cost, date_last_confirmed)
    SELECT           poi_id, title, town, town_normalisee, postcode, latitude, longitude, number_of_points, usage_cost, date_last_confirmed
    FROM poi_df
    ON CONFLICT (poi_id) DO UPDATE SET
        title = EXCLUDED.title,
        town = EXCLUDED.town,
        town_normalisee = EXCLUDED.town_normalisee,
        postcode = EXCLUDED.postcode,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        number_of_points = EXCLUDED.number_of_points,
        usage_cost = EXCLUDED.usage_cost,
        date_last_confirmed = EXCLUDED.date_last_confirmed
    """)

    logger.info(f"Insertion données dans la table POI : {poi_df.shape[0]} lignes traitées avec succès")



def creer_table_connections(con: DuckDBPyConnection) -> None:
    """Crée la table connections si elle n'existe pas déjà."""

    con.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            connection_id BIGINT PRIMARY KEY,
            poi_id BIGINT REFERENCES poi(poi_id),
            power_kw DOUBLE,
            amps BIGINT,
            voltage DOUBLE,
            connection_type VARCHAR,
            current_type VARCHAR,
            is_operational BOOLEAN,
            level_title VARCHAR,
            is_fast_charge_capable BOOLEAN
        )
    """)
    # Attention : Message à adapter pour bien faire comprendre le cas où la table existe déjà.
    logger.info("Table connections créée avec succès.")

def inserer_connections(con: DuckDBPyConnection, connections_df: pl.DataFrame) -> None:
    """Insère ou met à jour les données connections (upsert sur connection_id)."""
    con.execute("""
        INSERT INTO connections (connection_id, poi_id, power_kw, amps, voltage, connection_type, current_type, is_operational, level_title, is_fast_charge_capable)
        SELECT                   connection_id, poi_id, power_kw, amps, voltage, connection_type, current_type, is_operational, level_title, is_fast_charge_capable
        FROM connections_df
        ON CONFLICT (connection_id) DO UPDATE SET
            poi_id = EXCLUDED.poi_id,
            power_kw = EXCLUDED.power_kw,
            amps = EXCLUDED.amps,
            voltage = EXCLUDED.voltage,
            connection_type = EXCLUDED.connection_type,
            current_type = EXCLUDED.current_type,
            is_operational = EXCLUDED.is_operational,
            level_title = EXCLUDED.level_title,
            is_fast_charge_capable = EXCLUDED.is_fast_charge_capable
    """)

    logger.info(f"Insertion données dans la table Connections : {connections_df.shape[0]} lignes traitées avec succès")


def charger_openchargemap_dans_duckdb(
    con: DuckDBPyConnection,
    poi_df: pl.DataFrame,
    connections_df: pl.DataFrame,
) -> None:
    """Orchestre le chargement complet dans DuckDB : création des tables et upsert."""
    creer_table_poi(con)
    inserer_poi(con, poi_df)

    creer_table_connections(con)
    inserer_connections(con, connections_df)

    logger.info(f"Chargement DuckDB terminé : poi={poi_df.shape}, connections={connections_df.shape}")
