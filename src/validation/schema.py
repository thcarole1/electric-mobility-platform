"""Validation de schéma pour les DataFrames Polars avant écriture."""
import polars as pl


class SchemaValidationError(Exception):
    """Levée quand un DataFrame ne correspond pas au schéma attendu."""
    pass


def valider_schema(df: pl.DataFrame, schema_attendu: dict[str, pl.DataType], nom_table: str) -> None:
    """Vérifie que les colonnes du DataFrame ont bien les types attendus.

    Args:
        df: le DataFrame à valider.
        schema_attendu: dictionnaire {nom_colonne: type_attendu}.
        nom_table: nom de la table, utilisé dans le message d'erreur.

    Raises:
        SchemaValidationError: si une colonne manque ou a un type incorrect.
    """
    erreurs = []
    for colonne, type_attendu in schema_attendu.items():
        if colonne not in df.columns:
            erreurs.append(f"colonne '{colonne}' manquante")
            continue
        type_reel = df.schema[colonne]
        if type_reel != type_attendu:
            erreurs.append(
                f"colonne '{colonne}' : type {type_reel} au lieu de {type_attendu} attendu"
            )
    if erreurs:
        raise SchemaValidationError(
            f"Validation du schéma '{nom_table}' échouée : " + "; ".join(erreurs)
        )
