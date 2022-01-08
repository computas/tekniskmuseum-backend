# Use to create a hash and salt of a password that the python-lib can understand.
# The password can be manually inserted into the database for the admin-user
from werkzeug.security import generate_password_hash
from datetime import datetime,timezone, timedelta
pwd = generate_password_hash(
        "examplePassword", method="pbkdf2:sha256:200000", salt_length=128
    )
print(pwd)
