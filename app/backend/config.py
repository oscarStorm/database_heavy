import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3307"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "database_heavy")
    mysql_user: str = os.getenv("MYSQL_USER", "admin")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")


settings = Settings()

