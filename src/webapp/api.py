#! /usr/bin/env python
import uuid
import random
import time
import sys
import os
import storage
import models
from CustomVision.CV_classifier import CVClassifier
from io import BytesIO
from PIL import Image
from flask import Flask
from flask import request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy

# Global variables
app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
classifier = CVClassifier()


labels = [
    "ambulance",
    "bench",
    "circle",
    "drawings",
    "square",
    "star",
    "sun",
    "triangle",
]
timeLimit = 20


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/startGame")
def startGame():
    """
    Starts a new game. A unique token is generated to keep track
    of game. A random label is chosen for the player to draw.
    Startime is recorded to calculate elapsed time when the game ends.
    Name can be either None or a name and is not unique. Will be sent from frontend.
    """
    startTime = time.time()
    token = uuid.uuid4().hex
    label = random.choice(labels)
    name = None  # get name from POST request ?

    # function from models for adding to db
    models.insert_into_games(token, name, startTime, label)

    # data is stored in a json object and returned to frontend
    data = {
        "token": token,
        "label": label,
        "startTime": startTime,
    }

    return jsonify(data), 200


@app.route("/submitAnswer", methods=["POST"])
def submitAnswer():
    """
    Endpoint for user to submit drawing. Drawing is classified with Custom
    Vision.The player wins if the classification is correct and the time
    used is less than the time limit.
    """
    stopTime = time.time()
    if "file" not in request.files:
        return "No image submitted", 400
    image = request.files["file"]
    if not allowedFile(image):
        return "Image does not satisfy constraints", 415
    classification = classifier.predict_png(image)

    # get token from frontend
    token = request.values['token']
    # get values from function in models
    name, startTime, label = models.query_game(token)

    # This might be a proble if user has slow connection...
    # Stop time on first line of function instead
    timeUsed = stopTime - startTime
    bestGuess = max(classification, key=classification.get)
    hasWon = timeUsed < timeLimit and bestGuess == label
    storage.saveImage(image, label)
    data = {
        "classificaton": classification,
        "correctLabel": label,
        "hasWon": hasWon,
        "timeUsed": timeUsed,
    }
    score = 700
    # add to db with function from models
    models.insert_into_scores(name, score)
    return jsonify(data), 200


def clearTable(table):
    """
        Clear a table in the database and return the result of the action.
    """
    response = models.clear_table(table)
    return response


def classify(image):
    """
        Classify image with Azure Custom Vision.
    """
    # TODO: implement custom vision here
    label = random.choice(labels)
    confidence = random.random()
    return label, confidence


def allowedFile(image):
    """
    Check if image satisfies the constraints of Custom Vision.
    """
    if image.filename == "":
        return False

    # Check if the filename is of PNG type
    png = image.filename.endswith(".png") or image.filename.endswith(".PNG")
    # Ensure the file isn't too large
    too_large = len(image.read()) > 4000000
    # Ensure the file has correct resolution
    image.seek(0)
    height, width = Image.open(BytesIO(image.stream.read())).size
    image.seek(0)
    correct_res = (height >= 256) and (width >= 256)
    if not png or too_large or not correct_res:
        return False
    else:
        return True


if __name__ == "__main__":
    # creates table if does not exist
    models.createTables(app)

    app.run(debug=True)
