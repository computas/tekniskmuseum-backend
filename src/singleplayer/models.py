"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

import datetime
from werkzeug import exceptions as excp
from src.extensions import db
from src.models import LabelSuccess


def insert_into_label_success(
    label: str, is_success: bool, date: datetime.datetime
):
    if (
        isinstance(label, str)
        and isinstance(is_success, bool)
        and isinstance(date, datetime.datetime)
    ):
        try:
            label_success = LabelSuccess(
                label=label, is_success=is_success, attempt_time=date
            )
            db.session.add(label_success)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert label success:" + str(e))
    else:
        raise excp.BadRequest("Bad request")
