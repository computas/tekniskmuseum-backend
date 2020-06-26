from api import db


class Games(db.Model):

    token = db.Column(
        db.NVARCHAR,
        primary_key=True,
        #autoincrement=False
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
    with app.app_context():
        db.create_all()

def insertIntoGames(token, name, starttime, label):
    game = Games(token=token, name=name, starttime=starttime, label=label)
    db.session.add(game)
    db.session.commit()

def insertIntoScores(name, score):
    score = Scores(name=name, score=score)
    db.session.add(score)
    db.session.commit()

def queryGame(token):
    game = Games.query.filter_by(token=token)
    return game.name, game.starttime, game.label
    