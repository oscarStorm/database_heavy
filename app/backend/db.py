import pymysql
from pymysql.connections import Connection

from app.backend.config import settings


def get_connection() -> Connection:
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

