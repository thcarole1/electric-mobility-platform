# Electric Mobility Platform

Projet fil rouge de portfolio — Data Engineering AWS, autour de la mobilité
électrique et de l'énergie.

## Contexte

Projet évolutif construit dans le cadre d'une reconversion professionnelle
vers un poste de Data Engineer. Architecture locale d'abord (Python, DuckDB),
puis migration progressive vers AWS (S3, Lambda, Glue, Athena, Airflow, dbt).

Voir `docs/adr/` pour l'historique des décisions techniques (9 ADR à ce jour).

## Sources de données

- **Open Charge Map** — bornes de recharge (poi, connections), zone Paris
- **Open-Meteo** — météo historique horaire, sur un échantillon de POI

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev]"
```

Copier `.env.example` en `.env` et renseigner :
- `OCM_API_KEY` (clé Open Charge Map)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

## Tests

```bash
pytest tests/
```

## Structure

```
electric-mobility-platform/
├── data/
│   ├── raw/          # données brutes, non versionnées
│   ├── processed/    # données nettoyées, non versionnées
│   └── warehouse/    # base DuckDB, non versionnée
├── src/
│   ├── common/        # fonctions génériques d'E/S (fichiers, S3)
│   ├── ingestion/      # récupération des données depuis les APIs
│   ├── cleaning/       # nettoyage, normalisation, assemblage
│   ├── warehouse/      # chargement dans DuckDB
│   ├── simulation/     # (à venir) moteur de simulation de sessions de recharge
│   └── analytics/      # (à venir) requêtes et indicateurs
├── notebooks/           # exploration et exemples d'usage des modules
├── tests/
└── docs/
    └── adr/             # Architecture Decision Records
```

## Statut

✅ Phase 1 — Pipeline local + AWS (S3, IAM) fonctionnel, deux sources
intégrées, testé (ingestion, nettoyage, chargement DuckDB).

🚧 Phase 2 — Simulateur de sessions de recharge à construire.
