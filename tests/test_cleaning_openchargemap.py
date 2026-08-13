import polars as pl
from unittest.mock import Mock

from cleaning.openchargemap import (
    extraire_poi,
    extraire_connections,
    ajouter_town_normalisee,
    sauvegarder_parquet,
    nettoyer_openchargemap
)

def test_extraire_poi_extrait_les_bons_champs():
    donnees_test = [
        {
            "ID": 123,
            "AddressInfo": {
                "Title": "Test Site",
                "Town": "Paris",
                "Postcode": "75001",
                "Latitude": 48.85,
                "Longitude": 2.35,
            },
            "NumberOfPoints": 2,
            "UsageCost": "Free",
            "DateLastConfirmed": "2026-01-01T00:00:00Z",
        }
    ]

    resultat = extraire_poi(donnees_test)

    assert len(resultat) == 1
    assert resultat[0]["poi_id"] == 123
    assert resultat[0]["town"] == "Paris"

def test_extraire_connections_extrait_les_bons_champs():
    donnees_test = [
                        {
                        "ID": 123,
                        "Connections" : [
                                            {
                                                "ID": 456,
                                                "PowerKW" : 22,
                                                "Amps" : 120,
                                                "Voltage": 400,
                                                "ConnectionType": {
                                                    "Title": "CCS (Type 2)"
                                                },
                                                "CurrentType": {
                                                    "Title": "DC"
                                                },
                                                "StatusType": {
                                                    "IsOperational": True
                                                },
                                                "Level": {
                                                    "Title": "Level 3:  High (Over 40kW)",
                                                    "IsFastChargeCapable": True
                                                }
                                            }
                                        ]
                        }
                    ]

    resultat = extraire_connections(donnees_test)

    assert len(resultat) == 1
    assert resultat[0]["poi_id"] == 123
    assert resultat[0]["connection_id"] == 456
    assert resultat[0]["current_type"] == "DC"

def test_ajouter_town_normalisee_town_present():
        donnees_poi = {
                        "town" : "Paris",
                        "title" : "Montparnasse"
                       }

        poi_df = pl.DataFrame(donnees_poi)

        resultat = ajouter_town_normalisee(poi_df)

        assert resultat.shape[1] == len(donnees_poi) +1
        assert resultat["town_normalisee"][0] == "Paris"

def test_ajouter_town_normalisee_ville_inconnue_rejetee():
    donnees_poi = {
        "town": None,
        "title": "SAEMES | PARKING LAGRANGE"
    }

    poi_df = pl.DataFrame(donnees_poi)

    resultat = ajouter_town_normalisee(poi_df)

    assert resultat["town_normalisee"][0] is None

def test_ajouter_town_normalisee_town_absent():
        donnees_poi = {
                        "town" : None,
                        "title" : "Paris | Montparnasse"
                       }

        poi_df = pl.DataFrame(donnees_poi)

        resultat = ajouter_town_normalisee(poi_df)

        assert resultat.shape[1] == len(donnees_poi) +1
        assert resultat["town_normalisee"][0] == "Paris"

def test_sauvegarder_parquet_ecrit_le_bon_contenu(tmp_path):
    df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    chemin = tmp_path / "test.parquet"

    sauvegarder_parquet(df, chemin)

    assert chemin.exists()
    df_relu = pl.read_parquet(chemin)
    assert df_relu.equals(df)

def test_nettoyer_openchargemap(monkeypatch):
    mock_extraire_poi = Mock(return_value=[{"poi_id": 1, "town": "Paris"}])
    mock_ajouter_town = Mock(side_effect=lambda df: df)
    mock_extraire_connections = Mock(return_value=[{"connection_id": 1, "poi_id": 1}])

    monkeypatch.setattr("cleaning.openchargemap.extraire_poi", mock_extraire_poi)
    monkeypatch.setattr("cleaning.openchargemap.ajouter_town_normalisee", mock_ajouter_town)
    monkeypatch.setattr("cleaning.openchargemap.extraire_connections", mock_extraire_connections)

    poi_df, connections_df = nettoyer_openchargemap([{"ID": 123}])

    mock_extraire_poi.assert_called_once()
    mock_ajouter_town.assert_called_once()
    mock_extraire_connections.assert_called_once()
