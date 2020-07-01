from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Games(db.Model):
    """
       This is the Games model in the database. It is important that the
       inserted values match the column values. Token column value cannot
       be String when a long hex is given.
    """
    token = db.Column(
        db.NVARCHAR(450),
        primary_key=True,
    )
    name = db.Column(
        db.String(64),
    )
    starttime = db.Column(
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


def createTables(app):
    """
        The tables will be created if they do not already exist.
    """
    with app.app_context():
        db.create_all()


def insertIntoGames(token, name, starttime, label):
    """
        Insert values into Games table.
    """
    game = Games(token=token, name=name, starttime=starttime, label=label)
    db.session.add(game)
    db.session.commit()


def insertIntoScores(name, score):
    """
        Insert values into Scores table.
    """
    score = Scores(name=name, score=score)
    db.session.add(score)
    db.session.commit()


def queryGame(token):
    """
        Return the first record of Games that matches the query.
    """
    try:
        game = Games.query.filter_by(token=token).first()
        return game.name, game.starttime, game.label
    except AttributeError:
        return "Could not find record for " + token + "."


def clearTable(table):
    """
        Clear the table sent as the argument and return a response
        corresponding to the result of the task.
    """
    try:
        if table == 'Games':
            Games.query.delete()
            db.session.commit()
        elif table == 'Scores':
            Scores.query.delete()
            db.session.commit()
    except AttributeError:
        db.session.rollback()
        return "Table does not exist."
