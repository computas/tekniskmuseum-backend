
# Classifier complaining about circular imports when not importing storage here
from webapp import storage
from webapp import models
from customvision.classifier import Classifier
from flask import Flask
from utilities.keys import Keys
from flask_cors import CORS
import csv


"""
Goal of this file is to browse through the dataset and find example images that the model predicts correctly. 
This is an important measure as not all the words from the google quickdraw dataset is 100% moderated, meaning
inappropriate content could appear in the dataset. As those drawings in general look nothing like the rest of the 
drawings in the dataset, they could be filtered out by prediction


WARNING: This script is very slow and isn't cheap, so it should be used thoughtfully. Also remember to point to the 
correct csv file with updated words.
"""
def main():
    app = Flask(__name__)
    if Keys.exists("CORS_ALLOWED_ORIGIN"):
        cors = CORS(app,
                    resources={r"/*": {"origins": Keys.get("CORS_ALLOWED_ORIGIN"),
                                    "supports_credentials": True}})
    else:
        cors = CORS(app, resources={
                    r"/*": {"origins": "*", "supports_credentials": True}})
    app.config.from_object("utilities.setup.Flask_config")

# Set up DB and models
    models.db.init_app(app)
    
    classifier = Classifier()

    # Take all words from first column of csv and print them as a list with " " around each word.
    # Open the CSV file
    with open('./dict_eng_to_nor_difficulties_v2.csv', 'r') as file:

        # Create a CSV reader object
        reader = csv.reader(file)
        words = [row[0] for row in reader]
    i = 1
    for word in words:
        print (f"Finding example images for word {word} ({i}/{len(words)})")
        images = classifier.classify_images_by_label(word, 50)
        with app.app_context():
            models.insert_into_example_images(images, word)
        i += 1

if __name__ == "__main__":
    main()