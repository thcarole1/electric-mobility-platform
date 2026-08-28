# Infrastructure as Code — Terraform

Gestion de l'infrastructure AWS de ce projet via Terraform. Toutes les
ressources listées ci-dessous ont été **importées** depuis une
infrastructure existante, créée manuellement dans un premier temps —
voir `docs/adr/` pour l'historique de cette création initiale.

## Structure

```
terraform/
├── main.tf              # point d'entrée, appelle les 4 modules
├── provider.tf           # configuration du provider AWS
├── variables.tf           # variables globales (clé API, sensible)
├── terraform.tfvars        # valeurs réelles des variables — jamais commité
└── modules/
    ├── network/            # VPC, sous-réseaux privés, security group,
    │                       # 10 VPC Endpoints, table de routage (socle MWAA)
    ├── iam/                 # 2 comptes IAM, 2 rôles, 2 politiques
    ├── data-lake/            # bucket S3, base Glue Catalog, Glue Crawler
    └── ingestion/             # 2 fonctions Lambda, 2 règles EventBridge Scheduler
```

## Prérequis

- Terraform >= 1.15
- Un compte AWS avec les permissions administrateur (`emp-admin` dans
  ce projet — jamais le compte applicatif `electric-mobility-pipeline`,
  dont les permissions sont trop restreintes pour gérer l'infrastructure)

## Configuration des credentials

Terraform lit les credentials AWS depuis les variables d'environnement
standard, jamais depuis un fichier du dépôt :

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

## Configuration de la clé API

Créer un fichier `terraform.tfvars` (exclu du dépôt via `.gitignore`) :

```hcl
ocm_api_key = "ta_cle_api_open_charge_map"
```

## Utilisation

```bash
terraform init      # télécharge le provider AWS, découvre les modules
terraform plan       # aperçu des changements — TOUJOURS avant apply
terraform apply       # applique réellement les changements sur AWS
```

⚠️ **Toujours lire attentivement la sortie de `terraform plan` avant
un `apply`.** Un symbole `-/+` (destroy puis create) sur une ressource
référencée ailleurs peut casser des dépendances — voir l'exemple
concret ci-dessous.

## Point d'attention découvert en pratique

Lors de l'import du security group MWAA, un `plan` a révélé un
`-/+ must be replaced` sur `aws_security_group.mwaa` — la description
du security group ne correspondait pas exactement à la valeur
existante, et ce champ ne peut pas être modifié en place chez AWS
(il force une destruction/recréation). Si appliqué tel quel, la
ressource aurait changé d'ID, cassant les 9 VPC Endpoints qui la
référençaient. Corrigé en alignant la description avant tout `apply`.
**Toujours lire un `-/+` comme un signal d'arrêt, pas juste une
modification anodine.**

## Ce qui n'est PAS géré par Terraform, volontairement

- **Le contenu du code Lambda** — les fonctions référencent un fichier
  `placeholder.zip` vide, avec `lifecycle { ignore_changes = [...] }`
  pour que Terraform ne touche jamais au code réel. Le déploiement du
  code reste géré par `scripts/build_lambda_*.sh`, cohérent avec la
  séparation infrastructure / code applicatif.
- **L'environnement MWAA lui-même** — le socle réseau (VPC, endpoints,
  security group) est bien sous Terraform, mais pas l'environnement
  MWAA. Deux endpoints VPC internes sont générés **dynamiquement** par
  AWS à chaque création d'environnement (voir ADR-021), rendant leur
  description a priori dans Terraform structurellement impossible sans
  un mécanisme en plusieurs passes.

## Roadmap

- ✅ Import complet de l'infrastructure existante (28 ressources)
- ✅ Réorganisation en modules
- ⬜ Docker (containerisation du pipeline)
- ⬜ CI/CD (GitHub Actions — tests automatiques, éventuel `terraform plan` sur PR)
