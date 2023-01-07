from prefect.storage import Azure
from prefect.run_configs import DockerRun
import os

azure_container = os.environ.get("AZURE_CONTAINER")
azure_store = Azure(container=azure_container)

env_label = os.environ.get("ENV_LABEL")

docker_run = DockerRun(
    image=os.environ.get("IMAGE_URL"),
    labels=["azure", env_label],
)
