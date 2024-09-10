from flask import Blueprint

multiplayer = Blueprint('multiplayer', __name__)


@multiplayer.route('/')
def home():
    return "Welcome to multiplayer"


@multiplayer.route('/pepe')
def home2():
    return "Welcome to multiplayer pepe"
