import pyodbc
import secrets



class Config():
    """ Config settings for flask and sqlalchemy should be set here."""

    #database config
    con_str=secrets.get('DB_CONNECTION_STRING')
    SQLALCHEMY_DATABASE_URI=con_str