"""Nettoyage et normalisation des données Open Charge Map."""

import logging
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)

VILLES_CONNUES = ["Paris"]

def sauvegarder_parquet(dataframe: pl.DataFrame, chemin: Path) -> None:
    """Sauvegarde un DataFrame Polars au format Parquet."""
    dataframe.write_parquet(chemin)
    logger.info(f"Données sauvegardées en Parquet en local : {chemin}")


def extraire_poi(donnees_json: list[dict]) -> list[dict]:
    """Extrait la table poi (champs plats) depuis le JSON brut."""
    table_poi = []
    for poi in donnees_json:
        poi_dict = {}
        poi_dict["poi_id"]              = poi["ID"]
        poi_dict["title"]               = poi["AddressInfo"]["Title"]
        poi_dict["town"]                = poi["AddressInfo"]["Town"]
        poi_dict["postcode"]            = poi["AddressInfo"]["Postcode"]
        poi_dict["latitude"]            = poi["AddressInfo"]["Latitude"]
        poi_dict["longitude"]           = poi["AddressInfo"]["Longitude"]
        poi_dict["number_of_points"]    = poi["NumberOfPoints"]
        poi_dict["usage_cost"]          = poi["UsageCost"]
        poi_dict["date_last_confirmed"] = poi["DateLastConfirmed"]
        table_poi.append(poi_dict)
    logger.info(f"Table poi extraite : {len(table_poi)} POI.")
    return table_poi


def extraire_connections(donnees_json: list[dict]) -> list[dict]:
    """Extrait la table connections (une ligne par connecteur) depuis le JSON brut."""
    table_connections =[]
    for poi in donnees_json:
        for connection in poi["Connections"]:
            connection_dict = {}
            connection_dict["poi_id"]  = poi["ID"]
            connection_dict["connection_id"] = connection["ID"]
            connection_dict["power_kw"] = connection["PowerKW"]
            connection_dict["amps"] = connection["Amps"]
            connection_dict["voltage"] = connection["Voltage"]
            connection_dict["connection_type"] = connection["ConnectionType"]["Title"]
            connection_dict["current_type"] = connection["CurrentType"]["Title"]
            connection_dict["is_operational"] = connection["StatusType"]["IsOperational"]
            connection_dict["level_title"] = connection["Level"]["Title"]
            connection_dict["is_fast_charge_capable"] = connection["Level"]["IsFastChargeCapable"]
            table_connections.append(connection_dict)
    logger.info(f"Table connections extraite : {len(table_connections)} connections.")
    return table_connections

def ajouter_town_normalisee(dataframe: pl.DataFrame) -> pl.DataFrame:
    """Ajoute une colonne town_normalisee, extraite de title quand town est absente.
    Seules les valeurs figurant dans VILLES_CONNUES sont acceptées comme ville valide."""
    dataframe = dataframe.with_columns(
        pl.when(
            (pl.col("town").is_null())
            & (pl.col("title").str.contains(" | ", literal=True))
            & (pl.col("title").str.split(" | ", literal=True).list.first().is_in(VILLES_CONNUES))
        )
        .then(pl.col("title").str.split(" | ", literal=True).list.first())
        .otherwise(pl.col("town"))
        .alias("town_normalisee")
    )
    nb_manquants = dataframe.select(pl.col("town_normalisee").is_null().sum()).item()
    logger.info(f"Colonne town_normalisee ajoutée : {nb_manquants} valeurs encore manquantes.")
    return dataframe


def nettoyer_openchargemap(donnees_json: list[dict]) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Orchestre le nettoyage complet : extraction poi + connections, normalisation town."""

    #Extrait la table poi (champs plats) depuis le JSON brut.
    poi = extraire_poi(donnees_json)
    poi_df = pl.DataFrame(poi)

    #Ajoute une colonne town_normalisee, extraite de title quand town est absente.
    poi_df = ajouter_town_normalisee(poi_df)

    #Extrait la table connections (une ligne par connecteur) depuis le JSON brut.
    connections = extraire_connections(donnees_json)
    connections_df = pl.DataFrame(connections)

    logger.info(f"Nettoyage réalisé avec succès. Résultat : {(poi_df.shape, connections_df.shape)}")

    return poi_df, connections_df
