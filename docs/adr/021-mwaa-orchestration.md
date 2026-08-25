# 021 — Orchestration Airflow/MWAA : mise en place et résolution d'une chaîne de blocages réseau et applicatifs

## Contexte

Rappelle-toi ADR-020 (script `run_pipeline.py`) et la roadmap Phase 3 —
Airflow/MWAA restait la dernière brique d'orchestration cloud non
abordée. Contrairement aux autres services du projet (Lambda, Glue,
Athena), MWAA s'est révélé être le chantier le plus long et le plus
complexe de tout le projet, réparti sur 6 sessions (17/08 au 25/08),
avec une dizaine de tentatives de création d'environnement.

## Décision

Traduction du pipeline (`run_pipeline.py`) en DAG Airflow
(`mwaa_dags/pipeline_electric_mobility.py`), avec 4 tâches séquentielles
(ingestion Open Charge Map, nettoyage + upload S3, ingestion météo,
assemblage + upload S3), passage de données entre tâches via XCom
(chemins S3) plutôt que via DataFrame en mémoire. Déploiement sur un
environnement MWAA (`mw1.micro`, Airflow 2.10.3) dans un VPC privé
sans accès Internet direct.

## Chronologie des blocages et résolutions

### 1. Endpoints VPC internes dynamiques (non documentés)

Au-delà des endpoints VPC standards (S3, ECR, KMS, SQS, monitoring,
logs, airflow.api/env/ops), MWAA génère deux endpoints **propres à
chaque tentative de création**, dont le nom de service n'existe qu'une
fois le provisionnement commencé
(`DatabaseVpcEndpointService`/`WebserverVpcEndpointService`,
récupérables via `aws mwaa get-environment`). Leur absence bloque
l'environnement en statut `PENDING` indéfiniment — comportement
documenté uniquement dans la référence SDK, jamais mentionné dans les
guides de configuration standards.

### 2. Collision de nom de module (`common/io.py`)

Le module `common/io.py` du projet entrait en collision avec le module
standard Python `io`, provoquant des erreurs d'import en cascade sur
tout Airflow. Résolu par un renommage complet (`common` → `emp_common`,
`io.py` → `storage.py`).

### 3. Rôle d'exécution créé sans politique attachée

Une tentative de création a échoué immédiatement
(`Provided role does not have sufficient permissions`) : MWAA avait
créé le rôle IAM demandé mais sans lui attacher de politique
(`aws iam list-role-policies` renvoyait une liste vide). Corrigé par
attachement manuel de la politique standard MWAA.

### 4. Script de build incrémental (résidu de collision)

Le script `build_mwaa_plugins.sh` faisait un `zip -r` sur un fichier
`plugins.zip` déjà existant, accumulant l'ancien `common/io.py` et le
nouveau `emp_common/storage.py` dans la même archive. Corrigé par
l'ajout d'un `rm -f plugins.zip` systématique avant reconstruction.

### 5. Conflit d'installation pip (`sqlalchemy`/`distutils`)

`requirements.txt` échouait avec `Cannot uninstall a distutils
installed project: 'sqlalchemy'` — comportement connu de pip depuis la
version 10 (issue pypa/pip #5247) face à un package pré-installé au
niveau système dans l'image de base MWAA.

### 6. Startup script : pas d'accès réseau au démarrage

Un startup script tentant `pip install` échouait avec `Network is
unreachable` — le script s'exécute avant que la connectivité réseau du
composant ne soit stable. Un simple `sleep 60` en préambule a permis
de débloquer l'installation sur le composant Webserver.

### 7. Isolation totale des environnements Python par composant

Découverte via recherche exhaustive dans les logs CloudWatch (aucune
occurrence de `pip3` dans les logs Worker/DAGProcessing, malgré un
succès confirmé sur le Webserver) : **chaque composant MWAA possède un
environnement Python totalement isolé**, sans aucune propagation entre
eux. Confirmé par le support AWS. Sur `mw1.micro`, la variable
d'environnement `MWAA_AIRFLOW_COMPONENT` vaut `hybrid` (pas `worker`)
pour le conteneur combiné scheduler+worker — information non
documentée, découverte en faisant afficher la variable elle-même.

### 8. Accès réseau public bloqué structurellement

Le fichier de contraintes (`raw.githubusercontent.com`) et les
packages PyPI (`pypi.org`) sont des ressources publiques hors AWS,
inaccessibles depuis un VPC privé sans NAT Gateway — même limitation
que pour l'API Open Charge Map elle-même (`api.openchargemap.io`).
Contourné dans un premier temps pour les dépendances Python en
pré-téléchargeant les wheels localement et en les hébergeant sur S3
(accessible via l'endpoint Gateway déjà en place), avec un startup
script conditionnel (`if MWAA_AIRFLOW_COMPONENT == "hybrid"`) qui les
télécharge via `boto3` (plus fiable que de supposer `aws-cli`
disponible) et les installe avec `pip3 install --no-index
--find-links=...`.

**Pour l'appel réel à l'API Open Charge Map**, ce contournement ne
suffisait pas — une vraie sortie Internet était nécessaire. Résolu par
l'ajout d'une **NAT Gateway** (sous-réseau public, Elastic IP,
route `0.0.0.0/0` ajoutée à la table de routage privée).

### 9. Permissions S3 incomplètes

Le rôle d'exécution n'avait que des permissions de lecture
(`s3:GetObject*`), pensées à l'origine pour le seul accès aux fichiers
DAG. Le DAG lui-même a besoin d'écrire (`s3:PutObject`) pour
l'ingestion. Politique complétée manuellement.

### 10. `storage_options` invalides pour Polars sur MWAA

Contrairement à `boto3.client("s3")` qui utilise automatiquement les
credentials du rôle IAM, Polars a besoin de `storage_options`
explicites. Le DAG utilisait `os.environ.get("AWS_ACCESS_KEY_ID")`,
variable inexistante sur MWAA (cohérent avec le principe de ne jamais
coder de clés AWS en dur). Corrigé en récupérant les credentials
temporaires du rôle via `boto3.Session().get_credentials()`.

## Outils de diagnostic ayant permis d'avancer

- **`verify_env.py`** (aws-support-tools, avec correctif d'un bug local
  `NameError` sur `self.check_service_vpc_endpoints`)
- **`AWSSupport-TroubleshootMWAAEnvironmentCreation`** (Systems Manager
  Automation) — test de connectivité réel entre ENI
- **AWS Support Case** (assistant IA puis potentiellement humain) — a
  fourni la découverte des endpoints internes dynamiques et confirmé
  l'isolation totale des environnements Python par composant

## Pourquoi

Chaque correction répondait à une contrainte réelle et vérifiée,
jamais à une supposition non testée — la méthode a systématiquement
été : reproduire l'erreur, chercher la preuve dans les logs (avec un
effort particulier sur la fiabilité de lecture — le copier-coller de
texte brut s'est avéré plus fiable que les pièces jointes dans cette
conversation), formuler une hypothèse, la vérifier avant d'agir. Cette
rigueur a payé : après un stade RETOUR ARRIÈRE réseau intermédiaire (le
NAT Gateway), le pipeline a fonctionné de bout en bout dès la
correction suivante.

## Conséquences

Le DAG `electric_mobility_pipeline` s'exécute avec succès sur MWAA
cloud (confirmé le 25/08/2026), produisant des fichiers Parquet à jour
sur S3 exactement comme `run_pipeline.py` en local. L'environnement
MWAA et la NAT Gateway ont été supprimés après validation, cohérent
avec le principe déjà établi (facturation continue, à ne conserver que
le temps de la démonstration). Pour retenter une démonstration future,
suivre le pense-bête `01_TECHNIQUE/ressources-apprentissage/Pense-bete-MWAA.md`
dans le vault Obsidian, qui documente l'intégralité de cette
chronologie avec les commandes exactes de chaque correction.

Ce chantier a représenté, de loin, l'investissement en temps le plus
important du projet — mais aussi la démonstration la plus complète
d'une compétence de diagnostic réseau/cloud complexe, potentiellement
la plus valorisable en entretien technique.
