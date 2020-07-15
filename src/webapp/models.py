"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

import datetime
import csv
import os
import random
from flask_sqlalchemy import SQLAlchemy
from werkzeug import exceptions as excp

DB = SQLAlchemy()


class Iteration(DB.Model):
    """
        Model for storing the currently used iteration of the ML model.
    """
    iteration_name = DB.Column(DB.String(64), primary_key=True)


class Games(DB.Model):
    """
       This is the Games model in the database. It is important that the
       inserted values match the column values. Token column value cannot
       be String when a long hex is given.
    """
    game_id = DB.Column(DB.NVARCHAR(32), primary_key=True)
    session_num = DB.Column(DB.Integer, default=1)
    labels = DB.Column(DB.String(64))
    date = DB.Column(DB.DateTime)


class Scores(DB.Model):
    """
        This is the Scores model in the database. It is important that the
        inserted values match the column values.
    """
    score_id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    name = DB.Column(DB.String(32))
    score = DB.Column(DB.Integer, nullable=False)
    date = DB.Column(DB.Date)


class PlayerInGame(DB.Model):
    """
        Table for attributes connected to a player in the game. game_id is a
        foreign key to the game table.
    """
    token = DB.Column(DB.NVARCHAR(32), primary_key=True)
    game_id = DB.Column(DB.NVARCHAR(32), nullable=False)
    play_time = DB.Column(DB.Float, nullable=False)


class Labels(DB.Model):
    """
        This is the Labels model in the database. It is important that the
        inserted values match the column values. This tabel is used for
        - translating english labels into norwgian
        - keeping track of all possible labels
    """
    english = DB.Column(DB.String(32), primary_key=True)
    norwegian = DB.Column(DB.String(32))


# Functions to manipulate the tables above
def create_tables(app):
    """
        The tables will be created if they do not already exist.
    """
    with app.app_context():
        DB.create_all()

    return True


def insert_into_games(game_id, labels, date):
    """
        Insert values into Games table.

        Parameters:
        game_id : random uuid.uuid4().hex
        labels: list of labels
        date: datetime.datetime
    """
    if (
        isinstance(game_id, str)
        and isinstance(labels, str)
        and isinstance(date, datetime.datetime)
    ):

        try:
            game = Games(game_id=game_id, labels=labels, date=date)
            DB.session.add(game)
            DB.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into games :" + str(e))
    else:
        raise excp.BadRequest(
            "game_id has to be string, labels has to be string "
            "and date has to be datetime.datetime."
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
            DB.session.add(score)
            DB.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into scores: " + str(e))
    else:
        raise excp.BadRequest(
            "Name has to be string, score can be int or "
            "float and date has to be datetime.date."
        )


def get_iteration_name():
    """
        Returns the first and only iteration name that should be in the model
    """

    iteration = Iteration.query.filter_by().first()
    assert iteration.iteration_name is not None
    return iteration.iteration_name


def update_iteration_name(new_name):
    """
        updates the one only iteration_name to new_name
    """
    iteration = Iteration.query.filter_by().first()
    if iteration is None:
        iteration = Iteration(iteration_name=new_name)
        DB.session.add(iteration)
    else:
        iteration.iteration_name = new_name

    DB.session.commit()
    return new_name


def insert_into_player_in_game(token, game_id, play_time):
    """
        Insert values into PlayerInGame table.

        Parameters:
        token: random uuid.uuid4().hex
        game_id: random uuid.uuid4().hex
        play_time: float
    """
    if (
        isinstance(token, str)
        and isinstance(game_id, str)
        and isinstance(play_time, float)
    ):
        try:
            player_in_game = PlayerInGame(
                token=token, game_id=game_id, play_time=play_time
            )
            DB.session.add(player_in_game)
            DB.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into games: " + str(e))
    else:
        raise excp.BadRequest(
            "Token has to be string, game_id has to be string "
            "and play time has to be float."
        )


def get_record_from_game(game_id):
    """
        Return the game record with the corresponding game_id.
    """
    game = Games.query.get(game_id)
    if game is None:
        raise excp.BadRequest("game_id invalid or expired")

    return game


def get_record_from_player_in_game(token):
    """
        Return the player in game record with the corresponding token.
    """
    player_in_game = PlayerInGame.query.get(token)
    if player_in_game is None:
        raise excp.BadRequest("Token invalid or expired")

    return player_in_game


# DELETABLE
def update_game(game_id, session_num, play_time):
    """
        Update game record for the incomming token with the given parameters.
    """
    try:
        game = Games.query.get(game_id)
        game.session_num += 1
        game.play_time = play_time
        DB.session.commit()
        return True
    except Exception:
        raise Exception("Couldn't update game.")


# ALTERNATIVE FUNC FOR UPDATE GAME TO ALSO WORK FOR MULTI
def update_game_for_player(game_id, token, session_num, play_time):
    """
        Update game and player_in_game record for the incomming game_id and
        token with the given parameters.
    """
    try:
        game = Games.query.get(game_id)
        game.session_num += 1
        player_in_game = PlayerInGame.query.get(token)
        player_in_game.play_time = play_time
        DB.session.commit()
        return True
    except Exception as e:
        raise Exception("Could not update game for player: " + str(e))


def delete_session_from_game(game_id):
    """
        To avoid unecessary data in the database this function is called by
        the api after a session is finished. The record in games table,
        connected to the particular game_id, is deleted.
    """
    try:
        game = Games.query.get(game_id)
        DB.session.query(PlayerInGame).filter(
            PlayerInGame.game_id == game_id
        ).delete()
        DB.session.delete(game)
        DB.session.commit()
        return "Record deleted."
    except AttributeError as e:
        DB.session.rollback()
        raise AttributeError("Couldn't find game_id: " + str(e))


def delete_old_games():
    """
        Delete records in games older than one hour.
    """
    try:
        games = (
            DB.session.query(Games)
            .filter(
                Games.date
                < (datetime.datetime.today() - datetime.timedelta(hours=1))
            )
            .all()
        )
        for game in games:
            DB.session.query(PlayerInGame).filter(
                PlayerInGame.game_id == game.game_id
            ).delete()
            DB.session.delete(game)

        DB.session.commit()
        return True
    except Exception as e:
        DB.session.rollback()
        raise Exception("Couldn't clean up old game records: " + str(e))


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

    except AttributeError as e:
        raise AttributeError(
            "Could not read daily highscore from database: " + str(e)
        )


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

    except AttributeError as e:
        raise AttributeError(
            "Could not read top high score from database: " + str(e)
        )


def drop_table(table):
    """
        Function for dropping a table, or all.
    """
    # Calling 'drop_table' with None as parameter means dropping all tables.
    DB.drop_all(bind=table)


def seed_labels(app, filepath):
    """
        Read file in filepath and upload to database
    """
    with app.app_context():
        if os.path.exists(filepath):
            # clear table
            Labels.query.delete()
            DB.session.commit()
            with open(filepath) as csvfile:
                try:
                    readCSV = csv.reader(csvfile, delimiter=",")

                    for row in readCSV:
                        insert_into_labels(row[0], row[1])
                except AttributeError as e:
                    raise AttributeError(
                        "Could not insert into games: " + str(e)
                    )

        else:
            raise AttributeError("File path not found")


def insert_into_labels(english, norwegian):
    """
        Insert values into Scores table.
    """
    if isinstance(english, str) and isinstance(norwegian, str):
        try:
            label_row = Labels(english=english, norwegian=norwegian)
            DB.session.add(label_row)
            DB.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into label: " + str(e))
    else:
        raise excp.BadRequest("English and norwegian must be strings")


def get_n_labels(n):
    """
        Reads all rows from database and chooses 3 random labels in a list
    """
    try:
        # read all english labels in database
        labels = Labels.query.all()
        english_labels = [str(label.english) for label in labels]
        random_list = random.sample(english_labels, n)
        return random_list

    except Exception as e:
        return Exception(
            "Could not read " + str(e) + " random rows from Labels table"
        )


def to_norwegian(english_label):
    """
        Reads the labels tabel and return the norwegian translation of the english word
    """
    try:
        norwegian_word = Labels.query.get(english_label)
        return norwegian_word

    except AttributeError as e:
        return AttributeError(
            "Could not find translation in Labels table: " + str(e)
        )
