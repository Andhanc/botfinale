import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = 8072195912


def get_db_url():
    return os.getenv(
        "DATABASE_URL",
        f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}/{os.getenv("POSTGRES_NAME")}',
    )
