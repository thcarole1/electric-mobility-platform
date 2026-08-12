#!/bin/bash
# scripts/build_lambda_openchargemap.sh
set -e

rm -rf lambda-package
mkdir -p lambda-package/common lambda-package/ingestion

cp src/common/__init__.py lambda-package/common/
cp src/common/io.py lambda-package/common/
cp src/ingestion/__init__.py lambda-package/ingestion/
cp src/ingestion/openchargemap.py lambda-package/ingestion/

cp lambda_functions/openchargemap_handler.py lambda-package/lambda_function.py

cd lambda-package
zip -r ../lambda-ingestion-openchargemap.zip .
cd ..

echo "Package prêt : lambda-ingestion-openchargemap.zip"
