import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_URI = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
TOKEN_TTL = 60
