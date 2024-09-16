# **Teknisk Museum Back-End**
_This repository contains source code and documentation for an API. It communicates through HTTP requests and serves as a backend for the project at Teknisk Museum. The API is concerned with single player mechanics, and doesn't use Websockets (like the multiplayer API), as synchronization between players isn't an issue in single player gameplay._
## **Usage**
The main entry point off the app is the bash script `startapp.sh`.
Just runing the script `bash startapp.sh` will launch the app.
The script accepts the following flags `bash startapp.sh <flag>`:

| Flag          | Result                                            |
|---------------|---------------------------------------------------|
| -h, --help    | display options                                   |
| -t, --test    | run PEP8 linter and unit tests                    |
| -d, --debug   | run locally with code reloading and test database |
| -w, --workers | specify number of workers                         |

### **Development**
* Clone repository.
* Install the database [driver](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15). Download version 17.
* Create virtual enviroment: `python3 -m venv venv`
* Activate virtual enviroment: `source venv/bin/activate`
* Install python requirements with pip: `pip install -r requirements.txt`.
* Save the secret keys as a json object in: `src/config.json`.
1. Head to portal.azure.com
2. Enter *KunstigeJens-Dev*
3. Under resources, go to *tekniskmuseumbackendsingleplayer-dev*
4. On the left column under settings, click *Environment variables*
5. Copy all the variables to the config file.
* Run script: `bash startapp.sh`to run the app (For windows users: Run this in a WSL shell).

### **Tests**
#### Run the tests with the following command:
* `bash startapp.sh -t`

### **Required Installation**

All python requirements should be included in `requirements.txt`, and can be installed by running
* `pip install -r requirements.txt`

## Debugging

There is a launch configuration in .vscode/launch.json that launches the app backend with debugpy. This is super helpful with debugging as you can set breakpoints and inspect variables etc. during runtime. 

**What you probably need to change is the "program" field to the path of your own gunicorn bin file.**

## Format & lint
Also in .vscode there is a tasks.json file that includes a task for formatting & linting which you should regularly do. The task uses autopep8 and flake8 using the .flake8 configuration files in the repo.

## **Migration of Images and Training the Model**

The backend is setup with scripts to use the image data from the QuickDraw dataset and process this. This includes transforming the image format from ndjson to png, uploading them to azure blob storage, and after that uploading it to Azure CustomVision for training.

This also assumes that both Azure Blob Storage and Azure CustomVision is already setup and running.

### **Downloading the dataset from Quickdraw and uploading it to blob storage**

1. Downloading the entire dataset can be done by cding into preprocessing, and running `gsutil -m cp gs://quickdraw_dataset/full/simplified/*.ndjson ./data`. The `*` can be replaced by the name of a category if you want to download just one specific category. If you want to only download the categories that are currently used in the game, you can run `bash download_quick_draw.sh` from the folder src/preprocessing. A csv-file with category names can also be provided as a command line argument to this script.

Note that the entire dataset is around ~22GB. More info on the dataset can be found on the [Github page](https://github.com/googlecreativelab/quickdraw-dataset#get-the-data).

Migrating the data to the Blob Storage is done in `src/preprocessing/data_migration.py`. This script uses the library *cairocffi* to transform the image vectors into pngs. This also requires to have *Cairo* Downloaded on the machine running the script. It is recommended to install this on either macOS or WSL.


2. Instructions for WSL/Ubuntu and macOS. 
    - On Ubuntu, run `sudo apt install libcairo2-dev pkg-config python3-dev`
    - On macOS/Homebrew, run `brew install cairo pkg-config`

While it is not the same python library, the documentation for [pycairo](https://pycairo.readthedocs.io/en/latest/getting_started.html) has some notes on installing Cairo.

3. Install the *cairocffi* package with `pip install cairocffi`

4. Run `bash upload_to_blob.sh`. This uploads images from the categories used in the current version of the game. You can also provide your own csv-file with
category names as a command line argument. Available options are 
  - `--categories`: should be a csv-file containing the categories you wish to upload.
  - `--num_images`: the number of images you want to upload from each category. The default is 50.

Assuming everything runs without errors, the images should now be in the blob storage

### **Uploading the data to Azure CustomVision and training an iteration of the classification model**

There is not a specific script to do this step, but both functions are ready for use in `src/customvision/classifier.py`. The classifier class is also initizalied in `src/webapp/api.py`, meaning the data can be uploaded and trained on there.

1. Add the lines for uploading images to api.py, so it looks something like the code below. "labels" is the list of labels to be trained on, e.g. ["airplane", "apple", "ant"]

        # Initialize CV classifier
        classifier = Classifier()
        classifier.upload_images(labels, "oldimgcontainer")

2. Run `startapp.sh` once, assuming the images gets uploaded without error, the upload_images line should be removed before running `startapp.sh` again later.

3. Go to [customvision.ai](customvision.ai), and click on the `Train` button in the top right after entering the correct project. For most use cases, `Quick Training` can be chosen here.




## **Conventions and Rules**

### **Coding Conventions**
_To make the code as easy to maintain and read as possible, it is necessary to follow some conventions. These conventions should be followed as strictly as possible to ensure that the process of code reviewing is as easy as possible._

#### **Code Convention Rules**
1. Use Pep8 as standard formatting for the code.
2. Ensure that the code is properly formatted before creating a merge request.
3. Avoid using magic numbers in the code. Create and retrieve variables through configuration files instead.
4. Comment the code properly when needed.
5. Include docstrings in functions where it's necessary, preferably always.
6. Develop tests when a new feature is implemented.
7. Don't EVER use 'import *'
8. Leave an empty line at the end of a statement, loop or a similiar code structure.
9. Don't use more than 1 newline between code chunks within functions/methods.
10. When creating strings, use double quotation marks ("string here") instead of single ('string here').
11. The triple quotations in a docstring should be on separate lines from the content. Remember to indent the content of the docstring as well. This makes it more readable.
12. Ideally, only a single class should be placed within each file.
13. Ensure that method names use underscores between words instead of camel case.

#### **Commit Message Rules**

1. Capitalize the Subject.
2. Do not end the Subject line with a period.
3. Use the present tense ("Add feature" not "Added feature").
4. Use the **imperative** mood ("Move cursor to..." not "Moves cursor to...").
5. Use the message body to explain what and why vs. how.

### **Branching**
_A rule of thumb when working on the project is to always branch out to a new branch when something is to be added. In general, developers shouldn't be able to push to master and therefore rely on submitting pull requests to put new features on the master branch._
#### **Branching Rules**
1. Use appropriate branch naming convention when creating a new branch (see the table below).
2. Create a new branch whenever something new is to be added.
3. Delete the branch when it has been successfully merged with the master branch.
4. Avoid repeating the same branch name over and over again.

#### **Branch naming**

| Naming                            | When to use?                                |
| ----------------------------------| ------------------------------------------- |
| `feature/awesome-branch-name`     | When developing a new feature               |
| `bugfix/awesome-branch-name`      | When fixing a bug                           |
| `docs/awesome-branch-name`        | When updating documentation                 |
| `refactoring/awesome-branch-name` | When refactoring code                       |
| `testing/awesome-branch-name`     | When writing new tests to existing features |

### **Pull Requests**
_When an issue has been solved and tested by the developer, a pull request must be submitted in the repository for validation. This is so the branch can be merged with the master branch. The Merge Request must follow the rules given below._
#### **Pull Request Rules**
1. Don't use the branch name as header for the pull request.
2. Use a header called "Changes" where you explain pointwise what the pull requests add to the project.
3. Add a header called "notes" where you explain things that may need attention, e.g if anything isn't finished, if something is broken etc.
4. Remember to rebase before creating the pull request.
5. There must be at least 2 approvals before the request can be merged.
6. The developer submitting the Merge Request is not allowed to approve the request (his/her vote doesn't count).
7. If the pull request resolves an issue submitted in the repository, the issue should be tagged in the pull request.
8. Use valid emojis to make the pull request more fun to read (not required, but recommended).

### **Issues**
_We generally want to write issues to keep track of tasks that need to be done. This means that if something is either lacking, or broken in the program, an issue can be submitted with a description of what needs to be done._

#### **Issue Rules**:
1. Be precise about what is needed to be done: <br/>
  1.1. What: Frontend, Backend, etc. <br/>
  1.2. Where: File that needs to be changed (also potentially function that needs editing). <br/>
  1.3. How: Potential solution or if a certain requirement must be satisfied (this can be vague, and may not be needed). <br/>
2. Don't describe multiple issues.
3. Follow the commit message rules when writing an issue.
4. The issue should be split up into two sections: One which explains the issue point-wise (if necessary), the second is for notes explaining potential solutions.

### **Rebasing**
_When rebasing, you will go through the commit history in your current branch and the master branch and sequentially pick what conflicting code to keep. You will do this after step 2 and step 4. Note that step 4 and step 5 may be repeated for each commit in the branch._

#### **Rebasing Steps:**
1. git checkout <branch_name>
2. git rebase master
3. git add .
4. git rebase --continue
5. git add .
5. git push --force
