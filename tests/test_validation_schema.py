import polars as pl
import pytest
from validation.schema import valider_schema, SchemaValidationError


def test_valider_schema_type_correct_ne_leve_rien():
    df = pl.DataFrame({"poi_id": [1, 2, 3], "title": ["a", "b", "c"]})
    schema_attendu = {"poi_id": pl.Int64, "title": pl.String}
    valider_schema(df, schema_attendu, "test_table")


def test_valider_schema_type_incorrect_leve_erreur():
    df = pl.DataFrame({"poi_id": ["1", "2", "3"]})
    schema_attendu = {"poi_id": pl.Int64}
    with pytest.raises(SchemaValidationError, match="poi_id"):
        valider_schema(df, schema_attendu, "test_table")


def test_valider_schema_colonne_manquante_leve_erreur():
    df = pl.DataFrame({"title": ["a", "b"]})
    schema_attendu = {"poi_id": pl.Int64, "title": pl.String}
    with pytest.raises(SchemaValidationError, match="manquante"):
        valider_schema(df, schema_attendu, "test_table")


def test_valider_schema_reproduit_incident_poi_id_meteo():
    """Reproduit precisement l'incident du 30/08 : poi_id contamine en
    String par le passage via XCom Airflow, non detecte avant Athena."""
    df = pl.DataFrame({
        "poi_id": ["7008", "6974"],
        "time": ["2026-01-01", "2026-01-01"],
        "temperature_2m": [15.0, 14.0],
    })
    schema_attendu = {"poi_id": pl.Int64, "time": pl.String, "temperature_2m": pl.Float64}
    with pytest.raises(SchemaValidationError):
        valider_schema(df, schema_attendu, "meteo")
