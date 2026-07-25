import time
import json
import pytest
from botocore.exceptions import ClientError
from unittest.mock import Mock
from ingestion.openchargemap import (
    generer_nom_fichier,
    appeler_api_openchargemap,
    sauvegarder_local,
    uploader_s3,
    ingerer_openchargemap)

# Tests - generer_nom_fichier
def test_generer_nom_fichier_contient_la_ville():
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

# Tests - appeler_api_openchargemap
def test_appeler_api_openchargemap_succes(monkeypatch):
    class FausseReponse:
        status_code = 200
        def json(self):
            return {"resultat": "donnees_test"}

    def faux_get(*args, **kwargs):
        return FausseReponse()

    monkeypatch.setattr("ingestion.openchargemap.requests.get", faux_get)

    resultat = appeler_api_openchargemap(48.85, 2.35, 5, "fausse_cle")
    assert resultat == {"resultat": "donnees_test"}

def test_appeler_api_openchargemap_retry_sur_erreur_serveur(monkeypatch):
    appels = []

    class FausseReponseErreur:
        status_code = 503
        text = "Service temporairement indisponible"

    def faux_get(*args, **kwargs):
        appels.append(1)
        return FausseReponseErreur()

    monkeypatch.setattr("ingestion.openchargemap.requests.get", faux_get)
    monkeypatch.setattr("ingestion.openchargemap.time.sleep", lambda x: None)

    resultat = appeler_api_openchargemap(48.85, 2.35, 5, "fausse_cle")

    assert resultat is None
    assert len(appels) == 3  # MAX_TENTATIVES

def test_appeler_api_openchargemap_pas_de_retry_sur_erreur_client(monkeypatch):
    appels = []

    class FausseReponseErreurClient:
        status_code = 401
        text = "Clé API invalide"

    def faux_get(*args, **kwargs):
        appels.append(1)
        return FausseReponseErreurClient()

    monkeypatch.setattr("ingestion.openchargemap.requests.get", faux_get)
    monkeypatch.setattr("ingestion.openchargemap.time.sleep", lambda x: None)

    resultat = appeler_api_openchargemap(48.85, 2.35, 5, "fausse_cle")

    assert resultat is None
    assert len(appels) == 1

# Tests sauvegarder_local
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

# Tests uploader_s3
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

# Tests ingerer_openchargemap
def test_ingerer_openchargemap_enchaine_toutes_les_etapes(monkeypatch, tmp_path):
    appels_sauvegarde = []
    appels_upload = []

    monkeypatch.setattr(
        "ingestion.openchargemap.appeler_api_openchargemap",
        lambda *args, **kwargs: {"donnees": "test"}
    )
    monkeypatch.setattr(
        "ingestion.openchargemap.sauvegarder_local",
        lambda donnees, chemin: appels_sauvegarde.append((donnees, chemin))
    )
    monkeypatch.setattr(
        "ingestion.openchargemap.uploader_s3",
        lambda chemin, bucket, cle, client: appels_upload.append((chemin, bucket, cle))
    )

    ingerer_openchargemap(
        latitude=48.85, longitude=2.35, distance=5, ville="paris",
        cle_api="fausse_cle", bucket_s3="mon-bucket", client_s3=Mock(),
        root_path=tmp_path,
    )

    assert len(appels_sauvegarde) == 1
    assert len(appels_upload) == 1

def test_ingerer_openchargemap_echec_API(monkeypatch, tmp_path):
    appels_sauvegarde = []
    appels_upload = []

    monkeypatch.setattr(
        "ingestion.openchargemap.appeler_api_openchargemap",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "ingestion.openchargemap.sauvegarder_local",
        lambda donnees, chemin: appels_sauvegarde.append((donnees, chemin))
    )
    monkeypatch.setattr(
        "ingestion.openchargemap.uploader_s3",
        lambda chemin, bucket, cle, client: appels_upload.append((chemin, bucket, cle))
    )

    ingerer_openchargemap(
        latitude=48.85, longitude=2.35, distance=5, ville="paris",
        cle_api="fausse_cle", bucket_s3="mon-bucket", client_s3=Mock(),
        root_path=tmp_path,
    )

    assert len(appels_sauvegarde) == 0
    assert len(appels_upload) == 0
