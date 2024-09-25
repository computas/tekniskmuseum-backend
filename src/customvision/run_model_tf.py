import tensorflow as tf
import numpy as np
import cv2
from PIL import Image


# These names are part of the model and cannot be changed.


def load_local_model():
    graph_def = tf.compat.v1.GraphDef()
    labels = []

    # These are set to the default names from exported models, update as needed.
    folder = "compact_model/"
    filename = f"{folder}saved_model.pb"
    labels_filename = f"{folder}labels.txt"

    # Import the TF graph
    with tf.io.gfile.GFile(filename, 'rb') as f:
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name='')

    # Create a list of labels.
    with open(labels_filename, 'rt') as lf:
        for label in lf:
            labels.append(label.strip())

    return labels


def predict_local_model(image):
    output_layer = 'loss:0'
    input_node = 'Placeholder:0'
    img = Image.open(image)  # Image.open(BytesIO(image.stream.read()))
    img = convert_to_opencv(img)
    img = img[:224, :224]  # this is silly. Is done to fit dimensions of input layer of the neural net.

    with tf.compat.v1.Session() as sess:
        try:
            prob_tensor = sess.graph.get_tensor_by_name(output_layer)
            predictions = sess.run(prob_tensor, {input_node: [img]})
            highest_probability_index = np.argmax(predictions)
            print('Classified as: ' + categories[highest_probability_index])
            print(f'With prob: {predictions[0][highest_probability_index]}')
            certainty = predictions
            best_certainty, best_guess = predictions[0][highest_probability_index], categories[highest_probability_index]
        except KeyError:
            print("Couldn't find classification output layer: " + output_layer + ".")
            print("Verify this a model exported from an Object Detection project.")
            #exit(-1)

    return best_certainty, best_guess


def convert_to_opencv(image):
    # RGB -> BGR conversion is performed as well.
    image = image.convert('RGB')
    r, g, b = np.array(image).T
    opencv_image = np.array([b, g, r]).transpose()
    return opencv_image


def resize_to_256_square(image):
    h, w = image.shape[:2]
    return cv2.resize(image, (256, 256), interpolation = cv2.INTER_LINEAR)
