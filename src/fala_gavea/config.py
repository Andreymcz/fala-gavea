import os

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
