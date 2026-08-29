# 024 — Intégration continue et backend distant Terraform

## Contexte

Après Terraform (ADR-022) et Docker (ADR-023), la dernière brique de
la Phase 5 (industrialisation) consistait à mettre en place une
intégration continue via GitHub Actions, pour automatiser la
vérification du code et de l'infrastructure à chaque changement.

## Décision

Deux workflows GitHub Actions ont été mis en place :

**`tests.yml`** — exécute les 63 tests unitaires du projet à chaque
push sur `main` et à chaque Pull Request visant `main`. Une règle de
protection de branche (ruleset) a été configurée pour empêcher toute
fusion tant que ce contrôle n'a pas réussi.

**`terraform-plan.yml`** — exécute `terraform init` et `terraform
plan` à chaque Pull Request modifiant des fichiers du dossier
`terraform/`, donnant un aperçu automatique de l'impact d'un
changement d'infrastructure avant fusion. Aucun `terraform apply`
n'est exécuté automatiquement : l'application des changements reste
une action manuelle, délibérément non automatisée pour cette
infrastructure sensible.

La mise en place de ce second workflow a nécessité de migrer le State
Terraform, jusqu'ici local et inaccessible à GitHub Actions, vers un
backend distant : un bucket S3 dédié (versionné), avec verrouillage
natif S3 (`use_lockfile`), remplaçant l'ancienne approche par table
DynamoDB devenue dépréciée depuis Terraform 1.10.

Les credentials AWS utilisés par ces workflows sont ceux du compte
administrateur (`emp-admin`), stockés comme secrets chiffrés GitHub
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `OCM_API_KEY`), jamais
en clair dans le code.

## Pourquoi

Le State local ne peut par nature être partagé entre l'environnement
de développement local et l'environnement d'exécution distant de
GitHub Actions. Un backend distant est la pratique standard du métier
dès qu'une infrastructure Terraform doit être consultée ou modifiée
depuis plusieurs environnements, indépendamment du nombre de personnes
impliquées.

L'absence délibérée d'un `terraform apply` automatique reflète une
pratique professionnelle courante : un plan d'infrastructure doit être
visible et vérifié avant toute application réelle, particulièrement
pour des ressources IAM, réseau ou de sécurité où un changement mal
anticipé peut avoir des conséquences en cascade — comme illustré par
l'incident du security group déjà documenté (ADR-022).

L'usage des credentials `emp-admin` plutôt qu'un rôle IAM restreint
dédié à la CI a été un choix assumé, motivé par la contrainte de temps
de la session, avec le risque correspondant explicitement identifié :
un compromis de ces secrets exposerait un accès administrateur complet
au compte AWS, plutôt qu'un accès limité au strict nécessaire.

## Conséquences

Une première tentative du workflow `terraform-plan.yml` a échoué avec
une erreur d'absence de credentials sur l'étape `terraform init` :
les variables d'environnement AWS n'étaient déclarées qu'au niveau de
l'étape `terraform plan`, alors que `init` lui-même nécessite un accès
au bucket S3 du backend. La correction a consisté à déplacer la
déclaration des credentials au niveau du job entier, les rendant
disponibles à toutes ses étapes.

Le périmètre du CI/CD mis en place reste volontairement partiel :
demeurent hors de ce périmètre le déploiement automatique du code
Lambda (toujours géré par les scripts de build existants, exécutés
manuellement), la publication d'image Docker sur un registre, et tout
mécanisme de `terraform apply` automatisé même avec approbation
préalable. Ce périmètre a été jugé suffisant pour démontrer les
compétences visées sans investissement de temps disproportionné par
rapport aux autres priorités du projet.
