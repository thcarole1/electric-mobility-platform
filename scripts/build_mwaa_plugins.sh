#!/bin/bash
set -e

rm -rf mwaa-plugins
rm -f plugins.zip
mkdir -p mwaa-plugins

cp -r src/emp_common mwaa-plugins/
cp -r src/ingestion mwaa-plugins/
cp -r src/cleaning mwaa-plugins/
cp -r src/warehouse mwaa-plugins/
cp -r src/simulation mwaa-plugins/
cp -r src/validation mwaa-plugins/

# Nettoyage des artefacts inutiles avant de zipper
find mwaa-plugins -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find mwaa-plugins -name "*.pyc" -delete
find mwaa-plugins -name "*:Zone.Identifier" -delete

cd mwaa-plugins
zip -r ../plugins.zip .
cd ..

echo "plugins.zip prêt"
