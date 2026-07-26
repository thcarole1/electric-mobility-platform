import pytest
import duckdb
import polars as pl

from warehouse.duckdb_loader import (
    creer_table_poi,
    inserer_poi,
    creer_table_connections,
    inserer_connections,
    charger_openchargemap_dans_duckdb)

@pytest.fixture
def con():
    connexion = duckdb.connect(":memory:")
    yield connexion
    connexion.close()

def test_creer_table_poi(con):
    creer_table_poi(con)
    resultat = con.execute("SELECT * FROM poi").fetchall()
    assert resultat == []

def test_creer_table_poi_nb_colonnes(con):
    creer_table_poi(con)
    resultat = con.execute("DESCRIBE poi").fetchall()
    assert len(resultat) == 10

def test_inserer_poi(con):
    creer_table_poi(con)

    poi_df_test = pl.DataFrame({
        "poi_id": [1],
        "title": ["Test"],
        "town": ["Paris"],
        "town_normalisee": ["Paris"],
        "postcode": ["75001"],
        "latitude": [48.85],
        "longitude": [2.35],
        "number_of_points": [1],
        "usage_cost": ["Free"],
        "date_last_confirmed": ["2026-01-01"],
    })

    inserer_poi(con, poi_df_test)

    resultat = con.execute("SELECT poi_id, title FROM poi").fetchall()
    assert resultat == [(1, "Test")]


def test_inserer_poi_upsert(con):
    creer_table_poi(con)

    poi_df_v1 = pl.DataFrame({
        "poi_id": [1],
        "title": ["Ancien nom"],
        "town": ["Paris"],
        "town_normalisee": ["Paris"],
        "postcode": ["75001"],
        "latitude": [48.85],
        "longitude": [2.35],
        "number_of_points": [1],
        "usage_cost": ["Free"],
        "date_last_confirmed": ["2026-01-01"],
    })

    inserer_poi(con, poi_df_v1)

    poi_df_v2 = poi_df_v1.with_columns(pl.lit("Nouveau nom").alias("title"))
    inserer_poi(con, poi_df_v2)

    resultat = con.execute("SELECT poi_id, title FROM poi").fetchall()
    assert resultat == [(1, "Nouveau nom")]


def test_creer_table_connections(con):
    creer_table_poi(con)
    creer_table_connections(con)
    resultat = con.execute("SELECT * FROM connections").fetchall()
    assert resultat == []


def test_inserer_connections(con):
    creer_table_poi(con)
    creer_table_connections(con)

    poi_df_test = pl.DataFrame({
        "poi_id": [1],
        "title": ["Test"],
        "town": ["Paris"],
        "town_normalisee": ["Paris"],
        "postcode": ["75001"],
        "latitude": [48.85],
        "longitude": [2.35],
        "number_of_points": [1],
        "usage_cost": ["Free"],
        "date_last_confirmed": ["2026-01-01"],
    })

    inserer_poi(con, poi_df_test)

    connections_df_test = pl.DataFrame({
        "connection_id": [1],
        "poi_id": [1],  # doit correspondre à un poi_id déjà présent dans la table poi (contrainte de clé étrangère)
        "power_kw": [22.0],
        "amps": [32],
        "voltage": [400.0],
        "connection_type": ["Type 2 (Socket Only)"],
        "current_type": ["AC (Three-Phase)"],
        "is_operational": [True],
        "level_title": ["Level 2 : Medium (Over 2kW)"],
        "is_fast_charge_capable": [False],
    })

    inserer_connections(con, connections_df_test)

    resultat = con.execute("SELECT connection_id, connection_type FROM connections").fetchall()
    assert resultat == [(1, "Type 2 (Socket Only)")]


def test_inserer_connections_poi_id_inexistant(con):
    creer_table_poi(con)
    creer_table_connections(con)

    connections_df_test = pl.DataFrame({
        "connection_id": [1],
        "poi_id": [999],
        "power_kw": [22.0],
        "amps": [32],
        "voltage": [400.0],
        "connection_type": ["Type 2 (Socket Only)"],
        "current_type": ["AC (Three-Phase)"],
        "is_operational": [True],
        "level_title": ["Level 2 : Medium (Over 2kW)"],
        "is_fast_charge_capable": [False],
    })

    with pytest.raises(duckdb.ConstraintException):
        inserer_connections(con, connections_df_test)


def test_charger_openchargemap_dans_duckdb(con):
    poi_df_test = pl.DataFrame({
        "poi_id": [123],
        "title": ["Test"],
        "town": ["Paris"],
        "town_normalisee": ["Paris"],
        "postcode": ["75001"],
        "latitude": [48.85],
        "longitude": [2.35],
        "number_of_points": [1],
        "usage_cost": ["Free"],
        "date_last_confirmed": ["2026-01-01"],
    })

    connections_df_test = pl.DataFrame({
        "connection_id": [1],
        "poi_id": [123],
        "power_kw": [22.0],
        "amps": [32],
        "voltage": [400.0],
        "connection_type": ["Type 2 (Socket Only)"],
        "current_type": ["AC (Three-Phase)"],
        "is_operational": [True],
        "level_title": ["Level 2 : Medium (Over 2kW)"],
        "is_fast_charge_capable": [False],
    })

    charger_openchargemap_dans_duckdb(con, poi_df_test, connections_df_test)

    resultat_poi = con.execute("SELECT COUNT(*) FROM poi").fetchall()
    resultat_connections = con.execute("SELECT COUNT(*) FROM connections").fetchall()

    assert resultat_poi == [(1,)]
    assert resultat_connections == [(1,)]
