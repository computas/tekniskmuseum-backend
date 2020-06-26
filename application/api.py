import uuid
import random
import time
import sys
import os
import storage
from io import BytesIO
from PIL import Image
from flask import Flask
from flask import request
from flask import jsonify
import models
from flask_sqlalchemy import SQLAlchemy

# Global variables
app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)


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
    name = None # get name from POST request ?


    # function from models for adding to db
    models.insertIntoGames(token, name, startTime, label)


    #data is stored in a json object and returned to frontend
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
    if "file" not in request.files:
        return "No image submitted", 400
    image = request.files["file"]
    if not allowedFile(image):
        return "Image does not satisfy constraints", 415
    classification, certainty = classify(image)
  
    # get token from frontend
    token = request.values['token']
    # get values from function in models 
    name, startTime, label = models.queryGame(token)

    # This might be a proble if user has slow connection...
    # Stop time on first line of function instead
    timeUsed = time.time() - startTime
    hasWon = timeUsed < timeLimit and classification == label
    #storage.saveImage(image, label)
    data = {
        "classificaton": classification,
        "certainty": certainty,
        "correctLabel": label,
        "hasWon": hasWon,
        "timeUsed": timeUsed,
    }
    score = 700
    # add to db with function from models
    models.insertIntoScores(name, score)
    return jsonify(data), 200

#@app.route('/clearTable', methods=['POST'])
def clearTable(table):
    #table = request.values['table']
    response = models.clearTable(table)
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
    #creates table if does not exist
    models.createTables(app)

    
    app.run(debug=True)
