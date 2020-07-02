"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Games(db.Model):
    """
       This is the Games model in the database. It is important that the
       inserted values match the column values. Token column value cannot
       be String when a long hex is given.
    """
    __tablename__="Games"
    token = db.Column(
        db.NVARCHAR(50),
        primary_key=True,
    )
    start_time = db.Column(
        db.Float,
        nullable=False
    )
    label = db.Column(
        db.String(64),
        nullable=False
    )


class Scores(db.Model):
    """
        This is the Scores model in the database. It is important that the
        inserted values match the column values.
    """
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    name = db.Column(
        db.String(64),
    )
    score = db.Column(
        db.Integer,
        nullable=False
    )


def create_tables(app):
    """
        The tables will be created if they do not already exist.
    """
    with app.app_context():
        db.create_all()
        return "Models created!"

    return "Couldn't create tables.." 


def insert_into_games(token, start_time, label):
    """
        Insert values into Games table.
    """
    game = Games(token=token, start_time=start_time, label=label)
    db.session.add(game)
    db.session.commit()


def insert_into_scores(name, score):
    """
        Insert values into Scores table.
    """
    score = Scores(name=name, score=score)
    db.session.add(score)
    db.session.commit()


def query_game(table,token):
    """
        Return name, starttime and label of the first record of Games that
        matches the query.
    """
    try:
        game = Games.query.filter_by(token=token).first()
        return game.start_time, game.label
    except AttributeError:
        return "Could not find record for " + token + "."


def clear_table(table):
    """
        Clear the table sent as the argument and return a response
        corresponding to the result of the task.
    """
    try:
        if table == 'Games':
            Games.query.delete()
            db.session.commit()
            return "Table successfully cleared"
        elif table == 'Scores':
            Scores.query.delete()
            db.session.commit()
            return "Table successfully cleared"
    except AttributeError:
        db.session.rollback()
        return "Table does not exist."

def drop_table(table):
    """
        Function for dropping a table, or all.
    """
    # Calling 'drop_table' with None as parameter means dropping all tables.
    db.drop_all(bind=table)

def get_class_by_tablename(tablename):
  """Return class reference mapped to table.

  :param tablename: String with name of table.
  :return: Class reference or None.
  """
  for c in db.Model._decl_class_registry.values():
    print("C= " + str(c))
    if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
      return c
