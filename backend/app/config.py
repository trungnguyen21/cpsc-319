import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_URI = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
TOKEN_TTL = 60

# --------------------------------------------------------------------------- #
# Google Cloud / Vertex AI                                                      #
# Required .env vars:                                                           #
#   GCP_PROJECT_ID=your-gcp-project-id                                         #
#   GCP_LOCATION=us-central1   (or nearest Vertex AI region)                   #
# Authenticate locally: gcloud auth application-default login                  #
# --------------------------------------------------------------------------- #
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
GCP_LOCATION   = os.environ.get("GCP_LOCATION", "us-central1")
