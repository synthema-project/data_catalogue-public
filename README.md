# Data catalogue module

## Description

This project hosts the code for the data catalogue module of real data management workflow in Synthema.
Data catalogue component is responsible for:

* Saving dataset metadata to the catalogue
* Retrieving dataset metadata from the catalogue
* Deleting dataset metadata from the catalogue

### Structure

The data-catalogue module is structured in the following folders:

* The folder *src* provides utilities, datasets, models, fastapi, requirements and Dockerfile
* The folder *k8s* includes kubernetes manifests
* The folder *jenkins* contains the Jenkinsfile to run unit and functional tests. 

## Data-catalogue deployment

## License

This project is licensed under the [MIT License](LICENSE).

This project extends and uses the following Open Softwares, which are compliant with MIT License:

* FastAPI: MIT License
* Pandas: BSD License
* psycopg2-binary: PostgreSQL License
* Uvicorn: BSD License
* python-multipart: MIT License
* pytest: MIT License
* jsonschema: MIT License
* sqlalchemy: MIT License
* sqlmodel: MIT License
