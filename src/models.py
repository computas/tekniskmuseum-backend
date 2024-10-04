import datetime
from sqlalchemy import extract
from .extensions import db
from werkzeug import exceptions as excp
import csv
import os
import random
import json


class Iteration(db.Model):
    """
    Model for storing the currently used iteration of the ML model.
    """

    iteration_name = db.Column(db.String(64), primary_key=True)


class Games(db.Model):
    """
    This is the Games model in the database. It is important that the
    inserted values match the column values. player_id column value cannot
    be String when a long hex is given.
    """

    game_id = db.Column(db.NVARCHAR(32), primary_key=True)
    session_num = db.Column(db.Integer, default=1)
    labels = db.Column(db.String(64))
    date = db.Column(db.DateTime)
    difficulty_id = db.Column(
        db.Integer, db.ForeignKey("difficulty.id"), default=1
    )
    players = db.relationship(
        "Players", uselist=False, back_populates="game", cascade="all, delete"
    )
    mulitplay = db.relationship(
        "MulitPlayer",
        uselist=False,
        back_populates="game",
        cascade="all, delete",
    )


class Scores(db.Model):
    """
    This is the Scores model in the database. It is important that the
    inserted values match the column values.
    """

    score_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.NVARCHAR(32), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)
    difficulty_id = db.Column(
        db.Integer, db.ForeignKey("difficulty.id"), default=1
    )


class Players(db.Model):
    """
    Table for attributes connected to a player in the game. game_id is a
    foreign key to the game table.
    """

    player_id = db.Column(db.NVARCHAR(32), primary_key=True)
    game_id = db.Column(db.NVARCHAR(32), db.ForeignKey(
        "games.game_id"), nullable=False)
    state = db.Column(db.String(32), nullable=False)

    game = db.relationship("Games", back_populates="players")


class MulitPlayer(db.Model):
    """
    Table for storing players who partisipate in the same game.
    """

    game_id = db.Column(
        db.NVARCHAR(32), db.ForeignKey("games.game_id"), primary_key=True
    )
    player_1 = db.Column(db.NVARCHAR(32))
    player_2 = db.Column(db.NVARCHAR(32))
    pair_id = db.Column(db.NVARCHAR(32))

    game = db.relationship("Games", back_populates="mulitplay")


class Labels(db.Model):
    """
    This is the Labels model in the database. It is important that the
    inserted values match the column values. This tabel is used for
    - translating english labels into norwgian
    - keeping track of all possible labels
    """

    english = db.Column(db.String(32), primary_key=True)
    norwegian = db.Column(db.String(32))
    difficulty_id = db.Column(
        db.Integer, db.ForeignKey("difficulty.id"), default=1
    )


class User(db.Model):
    """
    This is user model in the database to store username and psw for
    administrators.
    """

    username = db.Column(db.String(64), primary_key=True)
    password = db.Column(db.String(256))


class Difficulty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.String(32), nullable=False)


class ExampleImages(db.Model):
    """
    Model for storing example image urls that the model has predicted correctly.
    """

    image = db.Column(db.String(256), primary_key=True)
    label = db.Column(db.String(32), db.ForeignKey("labels.english"))


class LabelSuccess(db.Model):
    """
    Model to keep track of success rates on each label
    """

    attempt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label = db.Column(db.String(32), db.ForeignKey("labels.english"))
    is_success = db.Column(db.Boolean)
    attempt_time = db.Column(db.DateTime)

    def get_success_rates_query():
        return """
                SELECT
                    label,
                CAST(SUM(CAST(is_success AS INT)) AS FLOAT) / COUNT(*) AS success_rate
                FROM
                    label_success
                GROUP BY
                    label
                ORDER BY
                    success_rate
                DESC
                """

    def insert_mock_data_query(label: str, is_success: bool):
        return f"""
                INSERT INTO
                    label_success (label, is_success, attempt_time)
                VALUES
                    ('{label}', {is_success}, GETDATE())
                """


def create_tables(app):
    """
    The tables will be created if they do not already exist.
    """
    with app.app_context():
        db.create_all()

    return True


def populate_difficulty(app):
    """
    Insert values into Difficulty table.
    """
    with app.app_context():
        if Difficulty.query.count() == 0:
            try:
                difficulty = Difficulty(difficulty="easy")
                db.session.add(difficulty)
                difficulty = Difficulty(difficulty="medium")
                db.session.add(difficulty)
                difficulty = Difficulty(difficulty="hard")
                db.session.add(difficulty)
                db.session.commit()
                return True
            except Exception as e:
                raise Exception(
                    "Could not insert into Difficulty table: " + str(e)
                )


def insert_into_scores(player_id, score, date, difficulty_id):
    """
    Insert values into Scores table.

    Parameters:
    player_id: player id, string
    score: float
    date: datetime.date
    """
    score_int_or_float = isinstance(score, float) or isinstance(score, int)

    if (
        isinstance(player_id, str)
        and score_int_or_float
        and isinstance(date, datetime.date)
        and isinstance(difficulty_id, int)
    ):
        try:
            score = Scores(
                player_id=player_id,
                score=score,
                date=date,
                difficulty_id=difficulty_id,
            )
            db.session.add(score)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into scores: " + str(e))
    else:
        raise excp.BadRequest(
            "Name has to be string, score can be int or "
            "float, difficulty_id has to be an integer 1-4 and date has to be datetime.date."
        )


def insert_into_games(game_id, labels, date, difficulty_id):
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
            game = Games(
                game_id=game_id,
                labels=labels,
                date=date,
                difficulty_id=difficulty_id,
            )
            db.session.add(game)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into games :" + str(e))
    else:
        raise excp.BadRequest(
            "game_id has to be string, labels has to be string "
            "and date has to be datetime.datetime."
        )


def get_iteration_name():
    """
    Returns the first and only iteration name that should be in the model.
    """
    iteration = Iteration.query.filter_by().first()
    assert iteration.iteration_name is not None
    return iteration.iteration_name


def update_iteration_name(new_name):
    """
    updates the one only iteration_name to new_name.
    """
    iteration = Iteration.query.filter_by().first()
    if iteration is None:
        iteration = Iteration(iteration_name=new_name)
        db.session.add(iteration)
    else:
        iteration.iteration_name = new_name

    db.session.commit()
    return new_name


def insert_into_players(player_id, game_id, state):
    """
    Insert values into Players table.

    Parameters:
    player_id: random uuid.uuid4().hex
    game_id: random uuid.uuid4().hex
    state: string
    """
    if (
        isinstance(player_id, str)
        and isinstance(game_id, str)
        and isinstance(state, str)
    ):
        try:
            player_in_game = Players(
                player_id=player_id, game_id=game_id, state=state
            )
            db.session.add(player_in_game)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into games: " + str(e))
    else:
        raise excp.BadRequest("All params has to be string.")


def insert_into_user(username, password):
    """
    Insert values into User table.
    """
    if isinstance(username, str) and isinstance(password, str):
        try:
            user = User(password=password, username=username)
            db.session.add(user)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into user: " + str(e))
    else:
        raise excp.BadRequest("Invalid type of parameters.")


def get_game(game_id):
    """
    Return the game record with the corresponding game_id.
    """
    game = Games.query.get(game_id)
    if game is None:
        raise excp.BadRequest("game_id invalid or expired")

    return game


def get_player(player_id):
    """
    Return the player in players record with the corresponding player_id.
    """
    player_in_game = Players.query.get(player_id)
    if player_in_game is None:
        raise excp.BadRequest("player_id invalid or expired")

    return player_in_game


def update_game_for_player(game_id, player_id, session_num, state):
    """
    Update game and player_in_game record for the incomming game_id and
    player_id with the given parameters.
    """
    try:
        game = Games.query.get(game_id)
        game.session_num += session_num
        player_in_game = Players.query.get(player_id)
        player_in_game.state = state
        db.session.commit()
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
        db.session.query(Players).filter(Players.game_id == game_id).delete()
        mp = MulitPlayer.query.get(game_id)
        if mp is not None:
            db.session.delete(mp)

        db.session.delete(game)
        db.session.commit()
        return True
    except AttributeError as e:
        db.session.rollback()
        raise AttributeError("Couldn't find game_id: " + str(e))


def delete_old_games():
    """
    Delete records in games older than one hour.
    """
    try:
        games = (
            db.session.query(Games)
            .filter(
                Games.date
                < (datetime.datetime.today() - datetime.timedelta(hours=1))
            )
            .all()
        )
        for game in games:
            db.session.query(Players).filter(
                Players.game_id == game.game_id
            ).delete()
            db.session.query(MulitPlayer).filter(
                MulitPlayer.game_id == game.game_id
            ).delete()
            db.session.delete(game)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise Exception("Couldn't clean up old game records: " + str(e))


def get_daily_high_score(difficulty_id):
    """
    Function for reading all daily scores.

    Returns list of dictionaries.
    """
    try:
        today = datetime.date.today()
        # filter by today and sort by score
        top_n_list = (
            Scores.query.filter_by(date=today, difficulty_id=difficulty_id)
            .order_by(Scores.score.desc())
            .all()
        )
        # structure data
        new = [
            {"id": score.score_id, "score": score.score}
            for score in top_n_list
        ]
        return new

    except AttributeError as e:
        raise AttributeError(
            "Could not read daily highscore from database: " + str(e)
        )


def get_top_n_high_score_list(top_n, difficulty_id):
    """
    Funtion for reading total top n list from database.

    Parameter: top_n, number of players in top list.

    Returns list of dictionaries.
    """
    try:
        # read top n high scores
        top_n_list = (
            Scores.query.filter_by(difficulty_id=difficulty_id)
            .order_by(Scores.score.desc())
            .limit(top_n)
            .all()
        )
        # structure data
        new = [
            {"id": score.score_id, "score": score.score}
            for score in top_n_list
        ]
        return new

    except AttributeError as e:
        raise AttributeError(
            "Could not read top high score from database: " + str(e)
        )

def get_games_played():
    """
    Function to get the total count of daily scores.

    Returns the count of scores as an integer.
    """
    try:
        today = datetime.date.today()
        # Filter by today's date
        score_count = (
            Scores.query.filter_by(date=today)
            .count()
        )

        return score_count

    except Exception as e:
        raise Exception(
            "Could not retrieve daily score count from the database: " + str(e)
        )
    
def get_games_played_per_month(month, year):
    """
    Function to get the total count of monthly played games.

    Returns the count of scores as an integer.
    """
    try:
        year = int(year)
        month = int(month)
        start_date = datetime.date(year, month, 1)
    
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        monthly_count = (
            Scores.query.filter(
                Scores.date >= start_date,
                Scores.date <= end_date
            )
            .count()
        )

        return monthly_count

    except Exception as e:
        raise Exception(
            "Could not retrieve score count from the database: " + str(e)
        )
    
def get_games_played_per_year(year):
    """
    Function to get the total count of yearly played games.

    Returns the count of scores as an integer.
    """
    try:
        year = int(year)
        yearly_count = (
            Scores.query.filter(extract('year', Scores.date) == year).count()
        )

        return yearly_count

    except Exception as e:
        raise Exception(
            "Could not retrieve count from the database: " + str(e)
        )

def clear_highscores():
    """
    Function for clearing score table.
    """
    Scores.query.delete()
    db.session.commit()


# User related functions
def get_user(username):
    """
    Return user record with corresponding username.
    """
    user = db.session.query(User).get(username)
    return user


def seed_labels(app, filepath):
    """
    Function for updating labels in database.
    """
    with app.app_context():
        if os.path.exists(filepath):
            with open(filepath) as csvfile:
                try:
                    readCSV = csv.reader(csvfile, delimiter=",")
                    for row in readCSV:
                        # Insert label into Labels table if not present
                        if Labels.query.get(row[0]) is None:
                            insert_into_labels(row[0], row[1], row[2])
                except AttributeError as e:
                    raise AttributeError(
                        "Could not insert into Labels table: " + str(e)
                    )
        else:
            raise AttributeError("File path not found")


def insert_into_labels(english, norwegian, difficulty_id):
    """
    Insert values into Scores table.
    """
    if isinstance(english, str) and isinstance(norwegian, str):
        try:
            label_row = Labels(
                english=english,
                norwegian=norwegian,
                difficulty_id=difficulty_id,
            )
            db.session.add(label_row)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into Labels table: " + str(e))
    else:
        raise excp.BadRequest("English and norwegian must be strings")


def get_n_labels(n, difficulty_id):
    """
    Reads all rows from database and chooses n random labels in a list.
    """
    try:

        # get labels from three most recent games
        games = (
            Games.query.filter(
                Games.difficulty_id <= difficulty_id,
                difficulty_id - Games.difficulty_id < 2,
            )
            .order_by(Games.date.desc())
            .limit(3)
            .all()
        )
        labels_to_filter = [
            label for game in games for label in json.loads(game.labels)
        ]

        # read all english labels in database
        labels = Labels.query.filter(
            Labels.difficulty_id <= difficulty_id
        ).all()
        english_labels = [str(label.english) for label in labels]

        minimum_labels = 6
        for label in labels_to_filter:
            if (
                label in english_labels
                and len(english_labels) > minimum_labels
            ):
                english_labels.remove(label)

        random_list = random.sample(english_labels, n)

        return random_list

    except Exception as e:
        raise Exception("Could not read Labels table: " + str(e))


def get_all_labels():
    """
    Reads all labels from database.
    """
    try:
        # read all english labels in database
        labels = Labels.query.all()
        return [str(label.english) for label in labels]

    except Exception as e:
        raise Exception("Could not read Labels table: " + str(e))


def get_labels_with_difficulty(difficulty):
    """
    Reads all labels from database with the given difficulty.
    """
    try:
        # read all english labels in database
        labels = Labels.query.filter_by(difficulty_id=difficulty).all()
        return [str(label.english) for label in labels]

    except Exception as e:
        raise Exception("Could not read Labels table: " + str(e))


def to_norwegian(english_label):
    """
    Reads the labels tabel and return the norwegian translation of the
    english word.
    """
    try:
        query = Labels.query.get(english_label)
        return str(query.norwegian)

    except AttributeError as e:
        raise AttributeError(
            "Could not find translation in Labels table: " + str(e)
        )


def to_english(norwegian_label):
    """
    Reads the labels table and return the english translation of the norwegian label
    """
    try:
        query = Labels.query.filter(Labels.norwegian == norwegian_label)[0]
        return str(query.english)

    except AttributeError as e:
        raise AttributeError(
            "Could not find translation in Labels table: " + str(e)
        )


def get_translation_dict():
    """
    Reads all labels from database and create dictionary.
    """
    try:
        labels = Labels.query.all()
        return dict(
            [(str(label.english), str(label.norwegian)) for label in labels]
        )
    except Exception as e:
        raise Exception("Could not read Labels table: " + str(e))


def delete_all_tables(app):
    """
    Function for deleting all tables in the database.
    Can use if you need to reset the database after adding new columns
    """
    with app.app_context():
        db.drop_all()
    return True


def insert_into_example_images(images, label):
    """
    Insert values into ExampleImages table.
    """
    if isinstance(images, list) and isinstance(label, str):
        try:
            for image in images:
                example_image = ExampleImages(image=image, label=label)
                db.session.add(example_image)
            db.session.commit()
        except Exception as e:
            raise Exception(
                "Could not insert into ExampleImages table: " + str(e)
            )
    else:
        raise excp.BadRequest("Invalid type of parameters.")


def get_n_random_example_images(label, number_of_images):
    """
    Returns n random example images for the given label.
    """
    try:
        example_images = ExampleImages.query.filter_by(label=label).all()
        selected_images = random.sample(
            example_images, min(number_of_images, len(example_images))
        )
        images = [image.image for image in selected_images]
        return images
    except Exception as e:
        raise Exception("Could not read ExampleImages table: " + str(e))


def populate_example_images(app):
    """
    Function for populating example images table with exported csv data. Used so you dont need to
    run the prediction job twice
    """
    with app.app_context():
        if ExampleImages.query.count() == 0:
            try:
                # read all rows from safe_images.csv
                base_dir = os.path.dirname(os.path.abspath(__file__))
                csv_file_path = os.path.join(
                    base_dir, "..", "example_images.csv"
                )
                with open(csv_file_path) as csvfile:
                    readCSV = csv.reader(csvfile, delimiter=",")
                    for row in readCSV:
                        example_image = ExampleImages(
                            image=row[0], label=row[1]
                        )
                        db.session.add(example_image)
                    db.session.commit()
                    app.logger.info("Example_Images table was populated. ")
            except Exception as e:
                raise Exception(
                    "Could not insert into ExampleImages table: " + str(e)
                )

def get_available_years():
    try:
        available_years = Scores.query.with_entities(db.extract('year', Scores.date).distinct()).all()
        years = [int(year[0]) for year in available_years]
        
        return years
    except Exception as e:
        raise Exception(
            "Could not get years: " + str(e)
        )