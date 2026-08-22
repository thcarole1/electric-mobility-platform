
import json
import time
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from emp_common.storage import (generer_nom_fichier,
                       sauvegarder_local,
                       uploader_s3,
                       sauvegarder_parquet_s3)


# --- generer_nom_fichier ---
def test_generer_nom_fichier_contient_lidentifiant():
    resultat = generer_nom_fichier("paris")
    assert "paris" in resultat

def test_generer_nom_fichier_contient_extract_json():
    resultat = generer_nom_fichier("paris")
    assert "_extract.json" in resultat

def test_generer_nom_fichier_differe_entre_deux_appels():
    resultat_1 = generer_nom_fichier("paris")
    time.sleep(1)
    resultat_2 = generer_nom_fichier("paris")
    assert resultat_1 != resultat_2

def test_generer_nom_fichier_suffixe_et_extension_personnalises():
    resultat = generer_nom_fichier("paris", suffixe="meteo", extension="csv")
    assert "_meteo.csv" in resultat

# --- sauvegarder_local ---
def test_sauvegarder_local_ecrit_le_bon_contenu(tmp_path):
    donnees = {"cle": "valeur"}
    chemin = tmp_path / "test.json"

    sauvegarder_local(donnees, chemin)

    assert chemin.exists()
    with open(chemin) as f:
        contenu = json.load(f)
    assert contenu == donnees

def test_sauvegarder_local_echoue_si_dossier_parent_absent(tmp_path):
    donnees = {"cle": "valeur"}
    chemin = tmp_path / "dossier_inexistant" / "test.json"

    with pytest.raises(FileNotFoundError):
        sauvegarder_local(donnees, chemin)

# --- uploader_s3 ---
def test_uploader_s3_appelle_upload_file(tmp_path):
    fichier_test = tmp_path / "test.json"
    fichier_test.write_text('{"cle": "valeur"}')

    client_mock = Mock()

    uploader_s3(fichier_test, "mon-bucket", "raw/test.json", client_mock)

    client_mock.upload_file.assert_called_once_with(str(fichier_test), "mon-bucket", "raw/test.json")

def test_uploader_s3_gere_client_error(tmp_path, caplog):
    fichier_test = tmp_path / "test.json"
    fichier_test.write_text('{"cle": "valeur"}')

    client_mock = Mock()
    client_mock.upload_file.side_effect = ClientError(
        error_response={"Error": {"Code": "403", "Message": "Accès refusé"}},
        operation_name="upload_file"
    )

    uploader_s3(fichier_test, "mon-bucket", "raw/test.json", client_mock)

    assert "Erreur AWS lors de l'upload" in caplog.text

def test_sauvegarder_parquet_s3_appelle_write_parquet():
    df_mock = Mock()
    storage_options = {
        "aws_access_key_id": "fake_key",
        "aws_secret_access_key": "fake_secret",
        "aws_region": "eu-west-3",
    }

    sauvegarder_parquet_s3(df_mock, "s3://mon-bucket/processed/poi/poi.parquet", storage_options)

    df_mock.write_parquet.assert_called_once_with(
        "s3://mon-bucket/processed/poi/poi.parquet",
        storage_options=storage_options
    )
