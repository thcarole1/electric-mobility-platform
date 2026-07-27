
"""Nettoyage et transformation des données météo Open-Meteo."""

import logging

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
