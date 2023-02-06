import os

from dotenv import load_dotenv
from fastapi import status
from fastapi.responses import JSONResponse

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = 50
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

ALGORITHM = os.getenv("ALGORITHM", default="HS256")
JWT_ACCESS_SECRET_KEY = os.getenv("JWT_ACCESS_SECRET_KEY", default="key")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", default="key")

POSTGRES_DB = os.getenv("POSTGRES_DB", default="postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", default="postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", default="localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", default="5432")

REDIS_HOST = os.getenv("REDIS_HOST", default="localhost")
REDIS_PORT = os.getenv("REDIS_PORT", default="6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

TESTING = os.getenv("TESTING", default="False")
if TESTING == "True":
    POSTGRES_SERVER = "db-test"
DATABASE_URL = (f"postgresql://{POSTGRES_USER}:"
                f"{POSTGRES_PASSWORD}@"
                f"{POSTGRES_SERVER}:"
                f"{POSTGRES_PORT}/"
                f"{POSTGRES_DB}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_URL = "media"
AVATAR_URL = "avatar"
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_URL)
TESTS_ROOT = os.path.join(BASE_DIR, "tests")
AVATAR_ROOT = os.path.join(BASE_DIR, MEDIA_URL, AVATAR_URL)

LIMIT = 15
LIMIT_MAX = 50

ALLOWED_TYPES = ("jpeg", "jpg", "png", "gif")
SIZES = [400, 100, 50]
INVALID_FILE = "Please upload a valid image."
INVALID_TYPE = "The type of the image couldn't be determined."

NOT_FOUND = JSONResponse({"detail": "NotFound"}, status.HTTP_404_NOT_FOUND)

TEST_HOST = "127.0.0.255"
