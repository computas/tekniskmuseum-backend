"""
    Configuration class for connecting to azure database.
"""

import sys
import os
from utilities.keys import Keys


class Config:
    """
        Config settings for flask and sqlalchemy should be set here.
    """

<<<<<<< HEAD
    if "pytest" in sys.modules:
        # Insert connection string for test database
        pass

    else:
        # Database configuration string
        con_str = Keys.get("DB_CONNECTION_STRING")
=======
    # Database configuration string
<<<<<<< HEAD
    con_str = keys.Keys.get("DB_CONNECTION_STRING")
>>>>>>> e68f56518d0d6af5dd065f53f72892c5ba050c03
=======
    con_str = Keys.get("DB_CONNECTION_STRING")
>>>>>>> d7ce184dc38ea03d6d9685e2db4fa81a3c31d3ae

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = con_str
