"""Génération de sessions de recharge simulées."""

import logging
import random
from datetime import date, datetime, timedelta

import polars as pl

logger = logging.getLogger(__name__)

POIDS_PAR_HEURE = {
    0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1,
    6: 2, 7: 3, 8: 3, 9: 2,
    10: 2, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2,
    16: 4, 17: 10, 18: 12, 19: 12, 20: 8,
    21: 4, 22: 2, 23: 1,
}


def generer_heure_debut() -> tuple[int, int]:
    """Génère une heure et une minute de début de session, pondérées vers la soirée."""
    heures = list(POIDS_PAR_HEURE.keys())
    poids = list(POIDS_PAR_HEURE.values())
    heure = random.choices(heures, weights=poids, k=1)[0]
    minute = random.randint(0, 59)
    return heure, minute


def generer_date_session(date_debut: date, date_fin: date) -> date:
    """Génère une date aléatoire entre date_debut et date_fin inclus."""
    nb_jours = (date_fin - date_debut).days
    decalage = random.randint(0, nb_jours)
    return date_debut + timedelta(days=decalage)


def combiner_date_heure(date_session: date, heure: int, minute: int) -> datetime:
    """Combine une date et une heure/minute en un objet datetime complet."""
    return datetime(date_session.year, date_session.month, date_session.day, heure, minute)


def recuperer_temperature(con, poi_id: int, horodatage_tronque: str) -> float | None:
    """Récupère la température pour un poi_id et un horodatage donnés, ou None si absente."""
    resultat = con.execute(
        "SELECT temperature_2m FROM meteo WHERE poi_id = ? AND time = ?",
        [poi_id, horodatage_tronque]
    ).pl()
    if resultat.is_empty():
        return None
    return resultat.item()


def generer_energie_cible(min_kwh: float = 5.0, max_kwh: float = 30.0) -> float:
    """Génère une énergie cible aléatoire, distribution uniforme."""
    return random.uniform(min_kwh, max_kwh)


def facteur_efficacite(temperature_c: float) -> float:
    """Renvoie un facteur d'efficacité de charge entre 0 et 1, réduit par le froid."""
    if temperature_c >= 20:
        return 1.0
    elif temperature_c >= 0:
        return 0.9
    else:
        return 0.75


def calculer_duree(energie_kwh: float, power_kw: float, temperature: float | None) -> float:
    """Calcule la durée de charge en heures, ajustée par la température."""
    if temperature is None:
        logger.warning("Température indisponible, utilisation d'une valeur par défaut (15°C).")
        temperature = 15.0

    efficacite = facteur_efficacite(temperature)
    return energie_kwh / (power_kw * efficacite)


def generer_session(
    con,
    connections_operationnelles: pl.DataFrame,
    date_debut: date,
    date_fin: date,
) -> dict:
    """Génère une session de recharge simulée complète."""
    connecteur = connections_operationnelles.sample(n=1).to_dicts()[0]

    heure_debut, minute_debut = generer_heure_debut()
    date_session = generer_date_session(date_debut, date_fin)
    date_heure_debut = combiner_date_heure(date_session, heure_debut, minute_debut)

    poi_id = connecteur["poi_id"]
    date_heure_debut_tronque = date_heure_debut.strftime("%Y-%m-%dT%H:00")
    temperature = recuperer_temperature(con, poi_id, date_heure_debut_tronque)

    energie_cible = generer_energie_cible()

    puissance = connecteur["power_kw"]
    duree = calculer_duree(energie_kwh=energie_cible, power_kw=puissance, temperature=temperature)

    date_heure_fin = date_heure_debut + timedelta(hours=duree)

    return {
        "connection_id": connecteur["connection_id"],
        "debut": date_heure_debut,
        "fin": date_heure_fin,
        "energie_kwh": energie_cible,
    }
