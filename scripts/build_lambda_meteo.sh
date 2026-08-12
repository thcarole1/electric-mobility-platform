#!/bin/bash
set -e

rm -rf lambda-package
mkdir -p lambda-package/common lambda-package/ingestion

cp src/common/__init__.py lambda-package/common/
cp src/common/io.py lambda-package/common/
cp src/ingestion/__init__.py lambda-package/ingestion/
cp src/ingestion/meteo.py lambda-package/ingestion/

cp lambda_functions/meteo_handler.py lambda-package/lambda_function.py

cd lambda-package
zip -r ../lambda-ingestion-meteo.zip .
cd ..

echo "Package prêt : lambda-ingestion-meteo.zip"
