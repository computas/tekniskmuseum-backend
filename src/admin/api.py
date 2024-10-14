from flask import Blueprint, current_app, request, session, jsonify
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageChops
from threading import Thread
from io import BytesIO
from src import storage
import pytz
import src.models as shared_models
from src.utilities import setup
from src.utilities.keys import Keys
from src.customvision.classifier import Classifier
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug import exceptions as excp
import requests

admin = Blueprint("admin", __name__)
classifier = Classifier()
norwegian_tz = pytz.timezone("Europe/Oslo")
log_pattern = r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2},\d{3}) (?P<level>[A-Z]+) (?P<message>.*)"


@admin.route("/auth", methods=["POST"])
def authenticate():
    """
    Endpoint for admin authentication. Returns encrypted cookie with login
    time and username.
    """
    set_config()
    username = request.values["username"]
    password = request.values["password"]

    user = shared_models.get_user(username)

    if user is None or not check_password_hash(user.password, password):
        raise excp.Unauthorized("Invalid username or password")

    session["last_login"] = datetime.now(norwegian_tz)
    session["username"] = username

    return json.dumps({"success": "OK"}), 200


@admin.route("/admin/getStatisticsPerMonth", methods=["GET"])
def monthly_statistics():
    is_authenticated()
    month = request.args.get('month')
    year = request.args.get('year')
    amount = shared_models.get_games_played_per_month(month, year)

    return json.dumps(amount), 200


@admin.route("/admin/getStatisticsPerYear", methods=["GET"])
def yearly_statistics():
    is_authenticated()

    year = request.args.get('year')
    amount = shared_models.get_games_played_per_year(year)

    return json.dumps(amount), 200


@admin.route("/getAvailableYears", methods=["GET"])
def get_available_years():
    try:
        available_years = shared_models.get_available_years()

        return jsonify(available_years), 200
    except Exception as e:
        return json.dumps({e}), 400


@admin.route("/admin/getPlayers", methods=["GET"])
def get_not_finished():
    try:
        is_authenticated()
        data = shared_models.get_not_finished_games()

        return json.dumps(data), 200
    except Exception as e:
        return json.dumps({e}), 400


@admin.route("/admin/getScoresPerMonth", methods=["GET"])
def get_count_per_month():
    """
    Endpoint to retrieve the amount of scores per month for a given year.
    """
    try:
        is_authenticated()
        year = request.args.get('year')
        year = int(year)
        count_list = shared_models.get_scores_count_per_month(year)

        return jsonify(count_list), 200
    except Exception as e:
        return json.dumps({e}), 400


@admin.route("/admin/<action>", methods=["GET", "POST"])
def admin_page(action):
    """
    Endpoint for admin actions. Requires authentication from /auth within
    SESSION_EXPIRATION_TIME
    """
    # Check if user has valid cookie
    is_authenticated()

    if action == "clearHighScore":
        shared_models.clear_highscores()
        return json.dumps({"success": "High scores cleared"}), 200

    elif action == "trainML":
        # Run training asynchronously
        Thread(target=classifier.retrain).start()
        return json.dumps({"success": "Training started"}), 200

    elif action == "hardReset":
        # Delete all images in CV, upload all orignal images and retrain
        classifier.delete_all_images()
        storage.clear_dataset()
        Thread(target=classifier.hard_reset_retrain).start()
        response = {"success": "All images deleted, model now training"}
        return json.dumps(response), 200

    elif action == "status":
        new_blob_image_count = storage.image_count()
        iteration = classifier.get_iteration()
        current_app.logger.info(shared_models.get_games_played())
        data = {
            "CV_iteration_name": iteration.name,
            "CV_time_created": str(iteration.created),
            "BLOB_image_count": new_blob_image_count,
        }
        return json.dumps(data), 200

    elif action == "logging":
        url = Keys.get("INSIGHTS_URL")

        headers = {
            "x-api-key": Keys.get("API_KEY"),
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            formatted_output = format_logs(data)
            return json.dumps(formatted_output), 200

        else:
            current_app.logger.error(
                f"Failed to get log from Azure: {response.text}"
            )
            return "Failed to fetch log from Azure", 500

    elif action == "logout":
        session.clear()
        return json.dumps({"success": "Session cleared"}), 200

    else:
        return json.dumps({"error": "Admin action unspecified"}), 400


def is_authenticated():
    """
    Check if user has an unexpired cookie. Renew time if not expired.
    Raises exception if cookie is invalid.
    """
    if "last_login" not in session:
        print("Login could not be found")
        raise excp.Unauthorized()

    session_length = datetime.now(norwegian_tz) - session["last_login"]
    is_auth = session_length < timedelta(minutes=setup.SESSION_EXPIRATION_TIME)

    if not is_auth:
        raise excp.Unauthorized("Session expired")
    else:
        session["last_login"] = datetime.now(timezone.utc)

        return True


@admin.errorhandler(Exception)
def handle_exception(error):
    """
    Captures all exceptions raised. If the Exception is a HTTPException the
    error message and code is returned to the client. Else the error is
    logged.
    """
    if isinstance(error, excp.HTTPException):
        # check if 4xx error. This should be returned to user.
        if error.code >= 400 and error.code < 500:
            return error
    else:
        current_app.logger.error(error)
        return json.dumps({"error": "Internal server error"}), 500


def set_config():
    session.clear()
    current_app.config.update(
        SECRET_KEY=os.urandom(24), SESSION_COOKIE_SECURE=True
    )


# Function to format the data
def format_logs(data):
    severity_mapping = {
        1: "INFO",
        2: "WARNING",
        3: "ERROR",
    }

    formatted_logs = []
    for row in data["tables"][0]["rows"]:
        timestamp, message, severity_level = row

        dt = datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")

        formatted_entry = {
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "level": severity_mapping.get(severity_level, "UNKNOWN"),
            "message": message.strip(),
        }

        formatted_logs.append(formatted_entry)

    return formatted_logs[::-1]
