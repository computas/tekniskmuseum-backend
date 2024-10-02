"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""

import datetime
import random
from src.extensions import db
from src.models import (
    MulitPlayer,
    Games,
    Players,
    Scores,
    Labels,
)
from src.utilities.exceptions import UserError
import uuid
import src.models as shared_models

"""
    Classes for describing tables in the database and additional functions for
    manipulating them.
"""


def insert_into_mulitplayer(game_id, player_id, pair_id):
    """
    Insert values into MulitPlayer table.

    Parameters:
    game_id: random uuid.uuid4().hex
    player_id: random uuid.uuid4().hex
    pair_id: string
    """
    pair_id_is_str_or_none = isinstance(pair_id, str) or pair_id is None
    if (
        isinstance(player_id, str)
        and pair_id_is_str_or_none
        and isinstance(game_id, str)
    ):
        try:
            mulitplayer = MulitPlayer(
                player_1=player_id,
                player_2=None,
                game_id=game_id,
                pair_id=pair_id,
            )
            db.session.add(mulitplayer)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into mulitplayer: " + str(e))
    else:
        raise UserError("All params has to be string.")


def check_player_2_in_mulitplayer(player_id, pair_id):
    """
    Function to check if player2 is none in database. If none, a player
    can be added to the game.
    """
    # If there is no rows with player_2=None, game will be None
    game = MulitPlayer.query.filter_by(player_2=None, pair_id=pair_id).first()
    if game is not None:
        if game.player_1 == player_id:
            raise UserError("you can't join a game with yourself")
        return game.game_id

    return None


def get_mulitplayer(game_id):
    """
    Return the mulitplayer with the corresponding game_id.
    """
    mp = MulitPlayer.query.get(game_id)
    if mp is None:
        raise UserError("game_id invalid or expired")

    return mp


def get_opponent(game_id, player_id):
    """
    Return the player in game record with the corresponding gameID.
    """
    mp = MulitPlayer.query.get(game_id)
    if mp is None:
        # Needs to be changed to socket error
        raise UserError("Token invalid or expired")
    elif mp.player_1 == player_id:
        if mp.player_2 is not None:
            return Players.query.get(mp.player_2)
        else:
            return None
    return Players.query.get(mp.player_1)


def update_game_for_player(game_id, player_id, increase_ses_num, state):
    """
    Update game and player record for the incoming game_id and
    player_id with the given parameters.
    """
    try:
        game = Games.query.get(game_id)
        game.session_num += increase_ses_num
        player = Players.query.get(player_id)
        player.state = state
        db.session.commit()
        return True
    except Exception as e:
        raise Exception("Could not update game for player: " + str(e))


def update_mulitplayer(player_2_id, game_id):
    """
    Update mulitplayer with player 2's id.
    """
    try:
        mp = MulitPlayer.query.get(game_id)
        player_1 = Players.query.get(mp.player_1)
        player_1.state = "Ready"
        mp.player_2 = player_2_id
        db.session.commit()
        return True
    except Exception as e:
        raise Exception("Could not update mulitplayer for player: " + str(e))


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
    Function for reading total top n list from database.

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
        new = [
            {"id": score.score_id, "score": score.score}
            for score in top_n_list
        ]
        return new

    except AttributeError as e:
        raise AttributeError(
            "Could not read top high score from database: " + str(e)
        )


def insert_into_labels(english, norwegian):
    """
    Insert values into Scores table.
    """
    if isinstance(english, str) and isinstance(norwegian, str):
        try:
            label_row = Labels(english=english, norwegian=norwegian)
            db.session.add(label_row)
            db.session.commit()
            return True
        except Exception as e:
            raise Exception("Could not insert into Labels table: " + str(e))
    else:
        raise UserError("English and norwegian must be strings")


def get_n_labels(n, difficulty_id):
    """
    Reads all rows from database and chooses n random labels in a list.
    """
    try:
        # read all english labels in database
        labels = Labels.query.filter(
            Labels.difficulty_id <= difficulty_id
        ).all()
        english_labels = [str(label.english) for label in labels]
        random_list = random.sample(english_labels, n)
        return random_list

    except Exception as e:
        raise Exception("Could not read Labels table: " + str(e))
