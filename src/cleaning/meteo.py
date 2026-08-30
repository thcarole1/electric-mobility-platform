
"""Nettoyage et transformation des données météo Open-Meteo."""

import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def extraire_meteo(donnees_json: dict) -> list[dict]:
    """Extrait une table plate (une ligne par heure) depuis la réponse Open-Meteo."""
    noms_variables = list(donnees_json["hourly"].keys())
    listes_valeurs = [donnees_json["hourly"][nom] for nom in noms_variables]

    resultat = []
    for valeurs in zip(*listes_valeurs):
        resultat.append(dict(zip(noms_variables, valeurs)))

    logger.info(f"Extraction météo effectuée avec succès : {len(resultat)} lignes extraites.")
    return resultat

def assembler_meteo_multi_poi(
    correspondance_poi_fichier: dict[int, str],
    root_path,
) -> list[dict]:
    """Assemble les données météo de plusieurs POI en une seule table plate,
    avec le poi_id associé à chaque ligne."""

    meteo_globale = []

    for poi_id, nom_fichier in correspondance_poi_fichier.items():
        chemin_local = root_path / "data" / "raw" / nom_fichier

        with open(chemin_local, "r") as f:
            donnees_json = json.load(f)

        lignes_extraites = extraire_meteo(donnees_json)

        for ligne in lignes_extraites:
            ligne["poi_id"] = int(poi_id)

        meteo_globale.extend(lignes_extraites)

    return meteo_globale
