"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

from flask_sqlalchemy import SQLAlchemy
import datetime


db = SQLAlchemy()


class Games(db.Model):
    """
       This is the Games model in the database. It is important that the
       inserted values match the column values. Token column value cannot
       be String when a long hex is given.
    """

    token = db.Column(db.NVARCHAR(32), primary_key=True,)
    start_time = db.Column(db.Float, nullable=False)
    label = db.Column(db.String(32), nullable=False)


class Scores(db.Model):
    """
        This is the Scores model in the database. It is important that the
        inserted values match the column values.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32))
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.date)


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
    if (isinstance(token, str) and isinstance(start_time, float)
            and isinstance(label, str)):
        try:
            game = Games(token=token, start_time=start_time, label=label)
            db.session.add(game)
            db.session.commit()
            return "Inserted"
        except AttributeError:
            raise AttributeError("Could not insert into games")
    else:
        raise AttributeError("Token has to be int, start time has to be float"
                             + ", label has to be string.")


def insert_into_scores(name, score, date):
    """
        Insert values into Scores table.
    """
    score_int_or_float = isinstance(score, float) or isinstance(score, int)
    if isinstance(name, str) and score_int_or_float and isinstance(date, datetime.date):
        try:
            score = Scores(name=name, score=score, date=date)
            db.session.add(score)
            db.session.commit()
            return "Inserted"
        except AttributeError:
            return AttributeError("Could not insert into scores")
    else:
        raise AttributeError("Name has to be string, score has to be float"
                             + " and date has to be datetime.")


def query_game(token):
    """
        Return name, starttime and label of the first record of Games that
        matches the query.
    """
    try:
        game = Games.query.filter_by(token=token).first()
        return game.start_time, game.label
    except AttributeError:
        raise AttributeError("Could not find record for " + token + ".")


def clear_table(table):
    """
        Clear the table sent as the argument and return a response
        corresponding to the result of the task.
    """
    try:
        if table == "Games":
            Games.query.delete()
            db.session.commit()
            return "Table successfully cleared"
        elif table == "Scores":
            Scores.query.delete()
            db.session.commit()
            return "Table successfully cleared"
    except AttributeError:
        db.session.rollback()
        return AttributeError("Table does not exist.")


def get_daily_high_score():
    """
        Function for reading all daily scores.

        Returns list of dictionaries.
    """

    try:
        today = str(datetime.date.today())

        #filter by today and sort by score
        top_n_list = Scores.query.filter_by(
            date=today).order_by(Scores.score).all()

        #structure data
        new = [{"name": player.name, "score": player.score}
               for player in top_n_list]

        return new

    except AttributeError:
        print("Could not read daily highscore from database")
        return AttributeError("Could not read daily highscore from database")


def get_top_n_high_score_list(top_n):
    """
        Funtion for reading overall top n list from database

        Returns list of dictionaries.
    """
    try:
        #read top n high scores
        top_n_list = Scores.query.order_by(
            Scores.score.desc()).limit(top_n).all()

        new = [{"name": player.name, "score": player.score}
               for player in top_n_list]

        return new

    except AttributeError:
        print("Could not read top " + str(top_n) + " high score from database")
        return AttributeError("Table does not exist.")


def drop_table(table):
    """
        Function for dropping a table, or all.
    """
    # Calling 'drop_table' with None as parameter means dropping all tables.
    db.drop_all(bind=table)


def get_size_of_table(table):
    if table == "Games":
        rows = db.session.query(Games).count()
        return rows
    elif table == "Scores":
        rows = db.session.query(Scores).count()
        return rows
