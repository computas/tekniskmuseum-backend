from classifier import Classifier
from src.utilities.keys import Keys
import sys

classifier = Classifier()
labels = sys.argv[1:]

classifier.upload_images(labels, Keys.get("CONTAINER_NAME"))
