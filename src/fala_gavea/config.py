import os

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./fala_gavea.db")
