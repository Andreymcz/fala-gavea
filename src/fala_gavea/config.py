import os

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./fala_gavea.db")
JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")
JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS: int = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
