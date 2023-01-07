# dp_ingest_salesforce_snowflake_pref

This repository contains prefect flow to ingest salesforce data into snowflake. 

The flow is deployed to QA when changes are merged to develop branch and deployed to Prod when changes are merged to master branch.

## Directory structure

  - flows ( folder containing prefect flows )
  - tasks ( folder containing prefect tasks )
  - utils ( folder containing prefect config )
  - azure_devops\azure-pipeline.yml ( azure devops pipeline yaml file that contains steps to deploy prefect flows )

## Prerequisites:

  - Prefect agent of type Docker running on Agent VM

## Steps to add additional salesforce objects

1. Pull the latest from develop and checkout new feature branch
2. Select objects to be added from master list
  
    - Select Salesforce objects to be loaded into Snowflake from salesforce_objects.csv

3. Install and configure tap-salesforce (this step is only needed if you don't already have tap-salesforce installed and configured locally).
    - On Windows use Ubunty wsl
    - Create new folder, for example, tap-salesforce. Go to new folder and open VS code from Ubuntu wsl.
      - mkdir tap-salesforce
      - cd tap-salesforce
      - code .
    - open bash terminal
      - virtualenv venv 
      - source venv/bin/activate 
      - pip install --upgrade pip 
      - pip install requests==2.20.0
      - pip install singer-python==5.10.0
      - pip install xmltodict==0.11.0
      - pip install tap-salesforce==SALESFORCE_PACKAGE_VERSION -i https://api:PROGET_API_KEY@proget.accruentsystems.com/pypi/dp.PyPI/simple

      Where:

      - SALESFORCE_PACKAGE_VERSION is the latest tap-salesforce version in ProGet: https://proget.accruentsystems.com/feeds/dp.PyPI. For example 22.9.14+master
      - PROGET_API_KEY is the ProGet api key from the vault: https://prod-vault.accruentsystems.com/ui/vault/secrets/nonprod/show/proget/general_api_key?namespace=dp

4. Run discovery
  
    - modify singer_config/source_salesforce_config.json - add new objects to the "white_list"
    - copy source_salesforce_config.json to tap-salesforce folder created at step 3
    - replace SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, and SALESFORCE_REFRESH_TOKEN with values from the Vault:
https://prod-vault.accruentsystems.com/ui/vault/secrets/nonprod/show/salesforce/api_user?namespace=dp
    
    - run catalog discovery: tap-salesforce -c source_salesforce_config.json -d > discover.json
    - replace discover.json with discover.json file generated during catalog discovery run.

5. Update source_salesforce_catalog.json
  
    - execute python .\create_catalog.py to update singer_catalog/qa/source_salesforce_catalog.json from discover.json. New salesforce objects will be marked as selected and incremental replication will be enabled.

6. Commit changes, push to remote, create pull request, complete peer review and merge to develop.