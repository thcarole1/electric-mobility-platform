from unittest.mock import Mock
import json

from cleaning.meteo import (extraire_meteo, assembler_meteo_multi_poi)

def test_extraire_meteo():
    donnees_test = {
                    "latitude": 48.89279,
                    "longitude": 2.2920206,
                    "generationtime_ms": 0.03838539123535156,
                    "utc_offset_seconds": 0,
                    "timezone": "GMT",
                    "timezone_abbreviation": "GMT",
                    "elevation": 36.0,
                    "hourly_units": {
                                    "time": "iso8601",
                                    "temperature_2m": "\u00b0C"
                                    },
                                    "hourly": {
                                                "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
                                                "temperature_2m": [15.5, 14.9]
                                                }
                    }

    resultat = extraire_meteo(donnees_test)

    assert len(resultat) == 2
    assert resultat[0]["time"] == "2026-07-20T00:00"
    assert resultat[0]["temperature_2m"] == 15.5
    assert resultat[1]["time"] == "2026-07-20T01:00"
    assert resultat[1]["temperature_2m"] == 14.9

def test_extraire_meteo_plusieurs_variables():
    donnees_test = {
                    "latitude": 48.89279,
                    "longitude": 2.2920206,
                    "generationtime_ms": 0.03838539123535156,
                    "utc_offset_seconds": 0,
                    "timezone": "GMT",
                    "timezone_abbreviation": "GMT",
                    "elevation": 36.0,
                    "hourly_units": {
                                    "time": "iso8601",
                                    "temperature_2m": "\u00b0C",
                                    "precipitation" :"mL"
                                    },
                                    "hourly": {
                                                "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
                                                "temperature_2m": [15.5, 14.9],
                                                "precipitation" : [0.0, 0.0],
                                                }
                    }

    resultat = extraire_meteo(donnees_test)

    assert len(resultat) == 2
    assert resultat[0]["time"] == "2026-07-20T00:00"
    assert resultat[0]["temperature_2m"] == 15.5
    assert resultat[0]["precipitation"] == 0.0
    assert resultat[1]["time"] == "2026-07-20T01:00"
    assert resultat[1]["temperature_2m"] == 14.9
    assert resultat[1]["precipitation"] == 0.0

def test_assembler_meteo_multi_poi(tmp_path):
    (tmp_path / "data" / "raw").mkdir(parents=True)

    donnees_poi_1 = {
        "hourly": {
            "time": ["2026-07-20T00:00"],
            "temperature_2m": [15.5],
        }
    }
    chemin_fichier_1 = tmp_path / "data" / "raw" / "fichier_poi_1.json"
    with open(chemin_fichier_1, "w") as f:
        json.dump(donnees_poi_1, f)

    correspondance_test = {123: "fichier_poi_1.json"}

    resultat = assembler_meteo_multi_poi(correspondance_test, tmp_path)

    assert len(resultat) == 1
    assert resultat[0]["poi_id"] == 123
    assert resultat[0]["temperature_2m"] == 15.5

def test_assembler_meteo_multi_poi_deux_poi(tmp_path):
    (tmp_path / "data" / "raw").mkdir(parents=True)

    donnees_poi_1 = {
        "hourly": {
            "time": ["2026-07-20T00:00"],
            "temperature_2m": [15.5],
        }
    }
    donnees_poi_2 = {
        "hourly": {
            "time": ["2026-07-20T00:00"],
            "temperature_2m": [10.5],
        }
    }
    chemin_fichier_1 = tmp_path / "data" / "raw" / "fichier_poi_1.json"
    chemin_fichier_2 = tmp_path / "data" / "raw" / "fichier_poi_2.json"

    with open(chemin_fichier_1, "w") as f:
        json.dump(donnees_poi_1, f)

    with open(chemin_fichier_2, "w") as f:
        json.dump(donnees_poi_2, f)

    correspondance_test = {
                            123: "fichier_poi_1.json",
                            456 : "fichier_poi_2.json"
                            }

    resultat = assembler_meteo_multi_poi(correspondance_test, tmp_path)

    assert len(resultat) == 2
    assert resultat[0]["poi_id"] == 123
    assert resultat[0]["temperature_2m"] == 15.5
    assert resultat[1]["poi_id"] == 456
    assert resultat[1]["temperature_2m"] == 10.5
