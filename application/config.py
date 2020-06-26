import pyodbc
import secrets

con_str=secrets.get('DB_CONNECTOR_STRING')


class Config():
    SQLALCHEMY_DATABASE_URI=con_str