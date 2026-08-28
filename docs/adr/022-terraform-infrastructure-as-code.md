# 022 — Infrastructure as Code avec Terraform

## Contexte

Après le README (rapide, haute valeur immédiate), l'industrialisation
restait le chantier le plus stratégique pour l'objectif Data Engineer,
avec trois briques prévues dans la roadmap Phase 5 : Terraform,
Docker, CI/CD. Jusqu'ici, toute l'infrastructure AWS du projet (VPC,
sous-réseaux, 10 endpoints, security group, comptes IAM, rôles,
politiques, 2 fonctions Lambda, 2 règles EventBridge, bucket S3, base
Glue Catalog, Glue Crawler) avait été créée **manuellement**, clic par
clic dans la console — cohérent avec l'approche pédagogique du projet,
mais sans aucune garantie de reproductibilité ni de protection contre
l'erreur humaine de configuration.

## Décision

Import de l'intégralité de l'infrastructure existante (28 ressources)
sous Terraform via `terraform import`, sans jamais recréer ni détruire
la moindre ressource réelle. Organisation en 4 modules cohérents :
- `network` (VPC, sous-réseaux privés, security group, 10 VPC
  Endpoints, table de routage — le socle réseau MWAA)
- `iam` (2 comptes IAM, 2 rôles, 2 politiques)
- `data-lake` (bucket S3, base Glue Catalog, Glue Crawler)
- `ingestion` (2 fonctions Lambda, 2 règles EventBridge Scheduler)

Le contenu du code Lambda (le zip déployé) reste volontairement en
dehors du périmètre Terraform — chaque fonction référence un
`placeholder.zip` vide avec `lifecycle { ignore_changes = [...] }`,
laissant `scripts/build_lambda_*.sh` gérer le déploiement de code
applicatif, cohérent avec le principe de séparer infrastructure et
code. La clé API Open Charge Map est injectée via une variable
Terraform `sensitive`, avec sa vraie valeur uniquement dans
`terraform.tfvars`, jamais commité.

## Pourquoi

L'import plutôt qu'une recréation permet de reprendre une
infrastructure existante sans interruption de service — un cas
réaliste et fréquent en entreprise, où Terraform n'est presque jamais
introduit sur un projet vierge. Chaque import a systématiquement été
suivi d'un `terraform plan` vérifié manuellement avant tout `apply`,
avec un principe strict : tout symbole `-/+` (destroy puis create) sur
une ressource impose un arrêt et une investigation avant de continuer,
jamais un `apply` réflexe.

La séparation en modules répartit les responsabilités selon leur
fonction réelle plutôt que leur simple appartenance à un même
service AWS — le bucket S3, bien qu'utilisé par plusieurs autres
parties du projet, reste une resource isolée dans `data-lake`
plutôt qu'un pseudo-module "S3", conformément au principe qu'un
module regroupe des ressources qui naissent et évoluent ensemble,
pas celles qui partagent simplement une technologie.

## Conséquences

Le premier `terraform plan` sur le security group MWAA a révélé un
`-/+ must be replaced`, provoqué par un écart de `description` non
modifiable en place chez AWS. Sans cette vérification systématique,
un `apply` aurait détruit et recréé ce security group avec un nouvel
ID, cassant instantanément les 9 VPC Endpoints Interface qui le
référençaient — un incident directement comparable, en gravité, aux
blocages réseau rencontrés pendant la mise en place de MWAA (voir
ADR-021), cette fois évité avant qu'il ne se produise plutôt que
diagnostiqué après coup.

Deux limites assumées restent hors du périmètre Terraform : le
contenu du code Lambda (géré par les scripts de build existants), et
l'environnement MWAA lui-même (dont deux endpoints VPC internes sont
générés dynamiquement par AWS à la création, rendant leur description
a priori structurellement impossible sans un mécanisme en plusieurs
passes — voir ADR-021 pour le détail).

La suite de la Phase 5 (Docker, CI/CD) sera traitée sur des branches
dédiées séparées, cohérent avec le principe qu'une branche représente
un changement complet et fonctionnellement indépendant, pas un
regroupement de sujets sans rapport direct entre eux.
