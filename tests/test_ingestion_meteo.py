import time
import json
import pytest
from botocore.exceptions import ClientError
from unittest.mock import Mock
from ingestion.meteo import (
        appeler_api_meteo,
        ingerer_meteo)

# Tests - appeler_api_meteo
def test_appeler_api_meteo_succes(monkeypatch):
    class FausseReponse:
        status_code = 200
        def json(self):
            return {"resultat": "donnees_test"}

    def faux_get(*args, **kwargs):
        return FausseReponse()

    monkeypatch.setattr("ingestion.meteo.requests.get", faux_get)

    resultat = appeler_api_meteo(48.85, 2.35, "2026-07-20","2026-07-24","temperature_2m")
    assert resultat == {"resultat": "donnees_test"}


def test_appeler_api_meteo_retry_sur_erreur_serveur(monkeypatch):
    appels = []

    class FausseReponseErreur:
        status_code = 503
        text = "Service temporairement indisponible"

    def faux_get(*args, **kwargs):
        appels.append(1)
        return FausseReponseErreur()

    monkeypatch.setattr("ingestion.meteo.requests.get", faux_get)
    monkeypatch.setattr("ingestion.meteo.time.sleep", lambda x: None)

    resultat = appeler_api_meteo(48.85, 2.35, "2026-07-20","2026-07-24","temperature_2m")

    assert resultat is None
    assert len(appels) == 3  # MAX_TENTATIVES

def test_appeler_api_meteo_pas_de_retry_sur_erreur_client(monkeypatch):
    appels = []

    class FausseReponseErreurClient:
        status_code = 401
        text = "Variable inexistante"

    def faux_get(*args, **kwargs):
        appels.append(1)
        return FausseReponseErreurClient()

    monkeypatch.setattr("ingestion.meteo.requests.get", faux_get)
    monkeypatch.setattr("ingestion.meteo.time.sleep", lambda x: None)

    resultat = appeler_api_meteo(48.85, 2.35, "2026-07-20","2026-07-24","erreur_variable")

    assert resultat is None
    assert len(appels) == 1

# Tests ingerer_meteo
def test_ingerer_meteo_enchaine_toutes_les_etapes(monkeypatch, tmp_path):
    appels_sauvegarde = []
    appels_upload = []

    monkeypatch.setattr(
        "ingestion.meteo.appeler_api_meteo",
        lambda *args, **kwargs: {"donnees": "test"}
    )
    monkeypatch.setattr(
        "ingestion.meteo.sauvegarder_local",
        lambda donnees, chemin: appels_sauvegarde.append((donnees, chemin))
    )
    monkeypatch.setattr(
        "ingestion.meteo.uploader_s3",
        lambda chemin, bucket, cle, client: appels_upload.append((chemin, bucket, cle))
    )

    ingerer_meteo(
        latitude=48.856614,
        longitude=2.352222,
        start_date="2026-07-20",
        end_date="2026-07-24",
        hourly="temperature_2m",
        identifiant="paris",
        bucket_s3="mon-bucket",
        client_s3=Mock(),
        root_path=tmp_path,
    )

    assert len(appels_sauvegarde) == 1
    assert len(appels_upload) == 1


def test_ingerer_meteo_echec_API(monkeypatch, tmp_path):
    appels_sauvegarde = []
    appels_upload = []

    monkeypatch.setattr(
        "ingestion.meteo.appeler_api_meteo",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "ingestion.meteo.sauvegarder_local",
        lambda donnees, chemin: appels_sauvegarde.append((donnees, chemin))
    )
    monkeypatch.setattr(
        "ingestion.meteo.uploader_s3",
        lambda chemin, bucket, cle, client: appels_upload.append((chemin, bucket, cle))
    )

    ingerer_meteo(
        latitude=48.856614,
        longitude=2.352222,
        start_date="2026-07-20",
        end_date="2026-07-24",
        hourly="temperature_2m",
        identifiant="paris",
        bucket_s3="mon-bucket",
        client_s3=Mock(),
        root_path=tmp_path,
    )

    assert len(appels_sauvegarde) == 0
    assert len(appels_upload) == 0
