# 023 — Containerisation du pipeline avec Docker

## Contexte

Après la mise en place de Terraform (ADR-022), la seconde brique de la
Phase 5 (industrialisation) consistait à containeriser le pipeline
local (`run_pipeline.py`), pour démontrer une compétence de
containerisation reproductible, indépendante de l'environnement
d'exécution.

## Décision

Construction d'un `Dockerfile` en deux étapes (multi-stage build) :
une première étape (`builder`) installe le projet et ses dépendances
Python, une seconde étape, repartant d'une image minimale, ne récupère
que le résultat de cette installation. Les credentials AWS et la clé
API ne sont jamais copiés dans l'image ; ils sont injectés à
l'exécution via `docker run --env-file`, avec un fichier local exclu
du dépôt (`.gitignore` élargi à `.env*`).

## Pourquoi

Le multi-stage build est une pratique standard de réduction de taille
d'image, testée dans ce projet : le gain constaté a été marginal
(842 Mo contre 827 Mo), parce que les bibliothèques principales
(`polars`, `duckdb`, `pyarrow`) sont distribuées sous forme de wheels
précompilées, sans nécessiter d'outils de compilation à éliminer entre
les deux étapes. La technique reste conservée malgré ce gain limité,
en tant que bonne pratique reconnue plutôt que pour son seul bénéfice
mesuré ici.

L'injection des credentials à l'exécution plutôt que leur inclusion
dans l'image respecte le même principe de sécurité appliqué sur
l'ensemble du projet : aucun secret ne doit jamais faire partie d'un
artefact construit ou versionné.

## Conséquences

Deux ajustements ont été nécessaires par rapport au fonctionnement en
environnement local classique :
- `python-dotenv`, présent uniquement dans les dépendances de
  développement du projet, a dû être ajouté explicitement à l'image,
  le code source appelant `load_dotenv()` sans condition
- Les dossiers `data/raw/` et `data/warehouse/`, jamais créés par le
  code lui-même (`sauvegarder_local` suppose leur existence
  préalable), ont dû être créés explicitement dans le `Dockerfile`
  — un comportement déjà identifié et documenté lors du déploiement
  initial des fonctions Lambda

Un incident de diagnostic a par ailleurs illustré une source d'erreur
extérieure au code et à la configuration Docker elle-même : un VPN
actif sur la machine hôte provoquait un timeout systématique du
handshake SSL vers l'API météo depuis le conteneur, alors que la
résolution DNS et la connexion TCP réussissaient normalement. La
désactivation du VPN a résolu le problème immédiatement, confirmant
que la cause était environnementale et non applicative.

Le pipeline containerisé produit des résultats strictement identiques
à l'exécution locale (50 POI, 99 connexions, 6000 lignes météo, 455
sessions), validant la reproductibilité recherchée par cette
containerisation.
