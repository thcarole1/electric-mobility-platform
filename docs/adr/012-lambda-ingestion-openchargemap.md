# 012 — Déploiement de l'ingestion Open Charge Map sur AWS Lambda

## Contexte

La roadmap Phase 3 prévoyait de faire tourner l'ingestion sur AWS
Lambda, première étape de l'extension du pipeline vers une architecture
plus automatisée et cloud-native, en préparation de l'orchestration
planifiée (EventBridge/Airflow).

## Décision

Déploiement de `ingestion/openchargemap.py` (et son module partagé
`common/io.py`) sur une fonction Lambda (`electric-mobility-ingestion-openchargemap`,
runtime Python 3.12), sans aucune modification du code métier. Seul un
nouveau fichier `lambda_function.py` (handler) a été ajouté, qui
construit le client S3 et appelle `ingerer_openchargemap(...)` avec les
paramètres adaptés à l'environnement Lambda.

Composants mis en place :
- Un rôle IAM dédié (`electric-mobility-lambda-role`), réutilisant la
  politique S3 déjà créée pour l'utilisateur IAM du laptop
  (`electric-mobility-s3-readwrite`), plus la politique gérée
  `AWSLambdaBasicExecutionRole` pour l'écriture des logs CloudWatch.
- Une Lambda Layer (`electric-mobility-ingestion-deps`, 588 Ko)
  contenant uniquement `requests` — dépendance strictement nécessaire à
  `ingestion/openchargemap.py`. `polars` a été explicitement écarté de
  cette Layer (219 Mo à lui seul), n'étant pas utilisé par ce module ;
  une Layer séparée sera créée si `cleaning/` ou `warehouse/` sont
  déployés sur Lambda un jour.
- La clé API Open Charge Map (`OCM_API_KEY`) est fournie via une
  variable d'environnement Lambda, plutôt qu'un fichier `.env`
  (inexistant nativement sur Lambda) ou AWS Secrets Manager (écarté
  pour ce stade du projet, comme la rotation de clés IAM classique
  documentée précédemment).
- Les identifiants AWS pour `boto3.client("s3")` ne sont plus fournis
  explicitement : le rôle IAM attaché à la fonction les injecte
  automatiquement dans l'environnement d'exécution.
- Le stockage local intermédiaire utilise `/tmp` (espace éphémère
  propre à Lambda), créé explicitement au démarrage du handler
  (`mkdir(parents=True, exist_ok=True)`), plutôt que `data/raw/` du
  dépôt qui n'existe pas dans cet environnement.
- Timeout de la fonction relevé de 3 secondes (valeur par défaut) à 30
  secondes, pour couvrir un appel API avec retry éventuel.

## Pourquoi

Le principe d'injection de dépendance appliqué depuis le début du
projet (secrets et clients externes toujours reçus en paramètre,
jamais construits à l'intérieur des fonctions métier) a permis un
déploiement sans aucune modification du code de `ingestion/openchargemap.py`
lui-même — seule la façon de construire ces paramètres a changé entre
l'environnement local et Lambda. Ce déploiement a aussi révélé un bug
de régression resté invisible en local : `ingerer_openchargemap` ne
renvoyait jamais le nom du fichier généré (contrairement à
`ingerer_meteo`, déjà corrigée précédemment), les deux fonctions ayant
divergé sans qu'aucun test ne le détecte, faute d'assertion sur la
valeur de retour de la première.

## Conséquences

Deux corrections apportées à `ingestion/openchargemap.py`, indépendantes
du travail Lambda lui-même mais découvertes à cette occasion :
suppression d'un import mort (`from dotenv import load_dotenv`, jamais
appelé, qui faisait échouer l'import sur Lambda faute de cette
dépendance dans la Layer) et ajout du `return nom_fichier` manquant
(avec mise à jour de la signature en `str | None` et des tests associés,
sur le modèle de `ingerer_meteo`).

Prochaine étape naturelle : déclenchement automatique via EventBridge
(planification récurrente), plutôt qu'une invocation manuelle depuis la
console. Le même schéma (Layer légère, rôle IAM dédié, variables
d'environnement pour les secrets tiers) sera réutilisé si `ingestion/meteo.py`
est déployée sur Lambda à son tour.
