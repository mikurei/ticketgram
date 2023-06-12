from models import sqlite_db, tables


def init_db() -> None:
    """Initializes the database entities"""
    sqlite_db.connect()
    sqlite_db.create_tables(tables)
    sqlite_db.close()
