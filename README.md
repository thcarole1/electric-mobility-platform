# Electric Mobility Platform

Projet fil rouge de portfolio — Data Engineering AWS, autour de la mobilité
électrique et de l'énergie.

## Contexte

Projet évolutif construit dans le cadre d'une reconversion professionnelle
vers un poste de Data Engineer. Architecture locale d'abord (Python, DuckDB),
puis migration progressive vers AWS (S3, Lambda, Glue, Athena, Airflow, dbt).

Voir `docs/adr/` pour l'historique des décisions techniques.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev]"
```

## Structure

```
electric-mobility-platform/
├── data/
│   ├── raw/          # données brutes, non versionnées
│   └── processed/    # données nettoyées, non versionnées
├── src/
│   ├── ingestion/     # récupération des données depuis les APIs
│   ├── cleaning/      # nettoyage et normalisation
│   ├── simulation/    # moteur de simulation de sessions de recharge
│   └── analytics/     # requêtes et indicateurs
├── notebooks/          # exploration
├── tests/
└── docs/
    └── adr/            # Architecture Decision Records
```

## Statut

🚧 Phase 0 — Cadrage initial en cours.
