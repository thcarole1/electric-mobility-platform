from collections import Counter
import polars as pl
import pytest
import duckdb
from datetime import date, datetime

from simulation.sessions import (
    facteur_efficacite,
    combiner_date_heure,
    calculer_duree,
    generer_energie_cible,
    generer_heure_debut,
    generer_date_session,
    generer_session)

from warehouse.duckdb_loader import (creer_table_meteo, creer_table_poi)

@pytest.fixture
def con():
    connexion = duckdb.connect(":memory:")
    yield connexion
    connexion.close()

# Fonctions déterministes
def test_facteur_efficacite_chaud():
    assert facteur_efficacite(25.0) == 1.0

def test_facteur_efficacite_tempere():
    assert facteur_efficacite(10.0) == 0.9

def test_facteur_efficacite_froid():
    assert facteur_efficacite(-5.0) == 0.75

def test_facteur_efficacite_limite_20():
    assert facteur_efficacite(20.0) == 1.0  # >= 20, donc chaud

def test_facteur_efficacite_limite_0():
    assert facteur_efficacite(0.0) == 0.9  # >= 0, donc tempéré

def test_combiner_date_heure():
    resultat = combiner_date_heure(date(2026, 7, 22), 18, 33)
    assert resultat == datetime(2026, 7, 22, 18, 33)

def test_calculer_duree_temperature_normale():
    duree = calculer_duree(energie_kwh=30, power_kw=3, temperature=25)
    assert duree == 10  # 30 / (3 * 1.0)

def test_calculer_duree_temperature_froide():
    duree = calculer_duree(energie_kwh=30, power_kw=3, temperature=-5)
    assert duree == 30 / (3 * 0.75)  # facteur d'efficacité réduit

def test_calculer_duree_temperature_none(caplog):
    duree = calculer_duree(energie_kwh=30, power_kw=3, temperature=None)
    assert duree == 30 / (3 * 0.9)  # valeur par défaut 15°C -> facteur 0.9
    assert "Température indisponible" in caplog.text

# Fonctions génératrices
def test_generer_energie_cible_dans_la_plage():
    for _ in range(100):
        energie = generer_energie_cible(min_kwh=5.0, max_kwh=30.0)
        assert 5.0 <= energie <= 30.0

def test_generer_energie_cible_bornes_personnalisees():
    for _ in range(100):
        energie = generer_energie_cible(min_kwh=10.0, max_kwh=15.0)
        assert 10.0 <= energie <= 15.0

def test_generer_heure_debut_dans_la_plage():
    for _ in range(100):
        heure, minute = generer_heure_debut()
        assert 0 <= heure <= 23 and 0 <= minute <= 59

def test_generer_heure_debut_pic_soiree_plus_frequent():
    heures_tirees = [generer_heure_debut()[0] for _ in range(1000)]
    comptage = Counter(heures_tirees)
    assert comptage[18] > comptage[3]

def test_generer_date_session_dans_la_plage():
    date_debut = date(2026, 7, 20)
    date_fin = date(2026, 7, 24)

    for _ in range(100):
        date_session = generer_date_session(date_debut, date_fin)
        assert date_debut <= date_session <= date_fin

def test_generer_session_structure(con):
    creer_table_poi(con)
    creer_table_meteo(con)

    connections_operationnelles = pl.DataFrame({
        "connection_id": [1],
        "poi_id": [198764],
        "power_kw": [7.0],
        "is_operational": [True],
    })

    session = generer_session(
        con,
        connections_operationnelles,
        date_debut=date(2026, 7, 20),
        date_fin=date(2026, 7, 24),
    )

    assert set(session.keys()) == {"connection_id", "debut", "fin", "energie_kwh"}
    assert session["connection_id"] == 1
    assert isinstance(session["debut"], datetime)
    assert isinstance(session["fin"], datetime)
    assert session["fin"] > session["debut"]
    assert isinstance(session["energie_kwh"], float)
    assert 5.0 <= session["energie_kwh"] <= 30.0
