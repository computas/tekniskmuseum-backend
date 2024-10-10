import csv

# Take all words from first column of csv and print them as a list with " " around each word.
# Open the CSV file
with open("./dict_eng_to_nor_difficulties_v2.csv", "r") as file:
    # Create a CSV reader object
    reader = csv.reader(file)

    # Extract the words from the first column and store them in a list
    words = [row[0] for row in reader]

    # Print the words as a list to use in classifier.upload_images() function
    print([f"{word}" for word in words])
