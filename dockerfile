FROM prefecthq/prefect

ARG STORAGE_CONNECTION_STRING=PRIVDED_BY_THE_PIPELINE

ARG IMAGE=PROVIDED_BY_THE_PIPELINE

ARG AZ_CLIENT_ID=PROVIDED_BY_THE_PIPELINE

ARG AZ_CLIENT_SECRET=PROVIDED_BY_THE_PIPELINE

ARG AZ_TENANT_ID=PROVIDED_BY_THE_PIPELINE

ARG AZ_CONTAINER_NAME=PROVIDED_BY_THE_PIPELINE

ARG AZ_SHARE_NAME=PROVIDED_BY_THE_PIPELINE

ARG RUN_ENVIRONMENT=PROVIDED_BY_THE_PIPELINE

ARG DOCKER_IMAGE_NAME=PROVIDED_BY_THE_PIPELINE

ARG DOCKER_SECRET_NAME=PROVIDED_BY_THE_PIPELINE

ARG AKS_CLUSTER_NAME=PROVIDED_BY_THE_PIPELINE

ARG AKS_CLUSTER_RESOURCE_GROUP_NAME=PROVIDED_BY_THE_PIPELINE

ARG AZ_PENDO_SHARE_NAME_SUB_PATH=PROVIDED_BY_THE_PIPELINE

ARG AZ_SALESFORCE_SHARE_NAME_SUB_PATH=PROVIDED_BY_THE_PIPELINE

ENV IMAGE_URL=$IMAGE

ENV AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION_STRING

ENV AZURE_CLIENT_ID=$AZ_CLIENT_ID

ENV AZURE_CLIENT_SECRET=$AZ_CLIENT_SECRET

ENV AZURE_TENANT_ID=$AZ_TENANT_ID

ENV AZURE_CONTAINER_NAME=$AZ_CONTAINER_NAME

ENV AZURE_SHARE_NAME=$AZ_SHARE_NAME

ENV RUN_ENVIRONMENT=$RUN_ENVIRONMENT

ENV DOCKER_IMAGE_NAME=$DOCKER_IMAGE_NAME

ENV DOCKER_SECRET_NAME=$DOCKER_SECRET_NAME

ENV AKS_CLUSTER_NAME=$AKS_CLUSTER_NAME

ENV AKS_CLUSTER_RESOURCE_GROUP_NAME=$AKS_CLUSTER_RESOURCE_GROUP_NAME

ENV AZURE_PENDO_SHARE_NAME_SUB_PATH=$AZ_PENDO_SHARE_NAME_SUB_PATH

ENV AZURE_SALESFORCE_SHARE_NAME_SUB_PATH=$AZ_SALESFORCE_SHARE_NAME_SUB_PATH

RUN mkdir -p /prefect/tasks/ /prefect/utils/ /prefect/state/ /prefect/logs/ /prefect/aks/ /prefect/aks/jobyaml/

COPY utils/ /prefect/utils/

COPY tasks/ /prefect/tasks/

COPY aks_job_creation_file/ /prefect/aks/

# copy kubectl for this image
COPY --from=lachlanevenson/k8s-kubectl:latest /usr/local/bin/kubectl /usr/local/bin/kubectl

ENV PYTHONPATH="${PYTHONPATH}:/prefect/tasks/:/prefect/utils/"

WORKDIR prefect

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN /bin/bash -c "pip install --upgrade pip && pip install -r requirements.txt"