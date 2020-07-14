"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug import exceptions as excp

db = SQLAlchemy()


class DataBaseException(Exception):
    """
        Custom exception for DB errors.
    """

    pass


class Iteration(db.Model):
    iteration_name = db.Column(db.String(64), primary_key=True)


class Games(db.Model):
    """
       This is the Games model in the database. It is important that the
       inserted values match the column values. Token column value cannot
       be String when a long hex is given.
    """

    token = db.Column(db.NVARCHAR(32), primary_key=True)
    session_num = db.Column(db.Integer, default=1)
    labels = db.Column(db.String(64))
    play_time = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime)


class Scores(db.Model):
    """
        This is the Scores model in the database. It is important that the
        inserted values match the column values.
    """

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32))
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)


# Functions to manipulate the tables above
def create_tables(app):
    """
        The tables will be created if they do not already exist.
    """
    with app.app_context():
        db.create_all()

    return True


def insert_into_games(token, labels, play_time, date):
    """
        Insert values into Games table.

        Parameters:
        token : random uuid.uuid4().hex
        labels: list of labels
        play_time : float
        date: datetime.datetime
    """
    if (
        isinstance(token, str)
        and isinstance(play_time, float)
        and isinstance(labels, str)
        and isinstance(date, datetime.datetime)
    ):
        try:
            game = Games(
                token=token, labels=labels, play_time=play_time, date=date
            )
            db.session.add(game)
            db.session.commit()
            return True
        except DataBaseException:
            raise DataBaseException("Could not insert into games")
    else:
        raise excp.BadRequest(
            "Token has to be string, start time has to be float"
            ", labels has to be string and date has to be datetime.date."
        )


def insert_into_scores(name, score, date):
    """
        Insert values into Scores table.

        Parameters:
        name: user name, string
        score: float
        date: datetime.date
    """
    score_int_or_float = isinstance(score, float) or isinstance(score, int)
    if (
        isinstance(name, str)
        and score_int_or_float
        and isinstance(date, datetime.date)
    ):
        try:
            score = Scores(name=name, score=score, date=date)
            db.session.add(score)
            db.session.commit()
            return True
        except DataBaseException:
            raise DataBaseException("Could not insert into scores")
    else:
        raise excp.BadRequest(
            "Token has to be string, start time has to be float"
            ", labels has to be string and date has to be datetime.date."
        )


def get_iteration_name():
    """
        Returns the first and only iteration name that should be in the model
    """

    iteration = Iteration.query.filter_by().first()

    assert iteration.iteration_name is not None

    return iteration.iteration_name


def update_iteration_name(new_name):
    iteration = Iteration.query.filter_by().first()

    # assert iteration.iteration_name is not None
    if iteration is None:
        iteration = Iteration(iteration_name=new_name)
        db.session.add(iteration)
    else:
        iteration.iteration_name = new_name

    db.session.commit()

    return new_name


def get_record_from_game(token):
    """
        Return name, starttime and label of the first record of Games that
        matches the query.
    """
    game = Games.query.get(token)
    if game is None:
        raise excp.BadRequest("Token invalid or expired")

    return game


def update_game(token, session_num, play_time):
    """
        Update game record for the incomming token with the given parameters.
    """
    try:
        game = Games.query.filter_by(token=token).first()
        game.session_num += 1
        game.play_time = play_time
        db.session.commit()
        return True
    except Exception:
        raise Exception("Couldn't update game.")


def delete_session_from_game(token):
    """
        To avoid unecessary data in the database this function is called by
        the api after a session is finished. All records in games table,
        connected to the particular token, is deleted.
    """
    try:
        game = Games.query.filter_by(token=token).first()
        db.session.delete(game)
        db.session.commit()
        return "Record connected to " + token + " deleted."
    except AttributeError:
        db.session.rollback()
        raise AttributeError("Couldn't find token.")


def delete_old_games():
    """
        Delete records in games older than one hour.
    """
    try:
        db.session.query(Games).filter(
            Games.date
            < (datetime.datetime.today() - datetime.timedelta(hours=1))
        ).delete()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise Exception("Couldn't clean up old game records:" + str(e))


def clear_table(table):
    """
        Clear the table sent as the argument and return a response
        corresponding to the result of the task.
    """
    try:
        if table == "Games":
            Games.query.delete()
            db.session.commit()
            return True
        elif table == "Scores":
            Scores.query.delete()
            db.session.commit()
            return True
    except AttributeError:
        db.session.rollback()
        return AttributeError("Table does not exist.")


def get_daily_high_score():
    """
        Function for reading all daily scores.

        Returns list of dictionaries.
    """
    try:
        today = datetime.date.today()
        # filter by today and sort by score
        top_n_list = (
            Scores.query.filter_by(date=today)
            .order_by(Scores.score.desc())
            .all()
        )
        # structure data
        new = [
            {"name": player.name, "score": player.score}
            for player in top_n_list
        ]
        return new

    except AttributeError:
        print("Could not read daily highscore from database")
        return AttributeError("Could not read daily highscore from database")


def get_top_n_high_score_list(top_n):
    """
        Funtion for reading tootal top n list from database.

        Parameter: top_n, number of players in top list.

        Returns list of dictionaries.
    """
    try:
        # read top n high scores
        top_n_list = (
            Scores.query.order_by(Scores.score.desc()).limit(top_n).all()
        )
        # strucutre data
        new = [
            {"name": player.name, "score": player.score}
            for player in top_n_list
        ]
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
    """
        Return size of table.
    """
    if table == "Games":
        rows = db.session.query(Games).count()
        return rows
    elif table == "Scores":
        rows = db.session.query(Scores).count()
        return rows
