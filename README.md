# **Teknisk Museum Back-End**
## **Usage**
### **Development**
_Guide on how to run the api in developer mode comes here!_

### **Tests**
_When running the tests, ensure that you are located in the same directory as this README._
#### Run the tests with the following command:
* pytest --ignore=training-tool

### **Required Installation**

All python requirements should be included in `requirements.txt`, and can be installed by running
* `pip install -r requirements.txt`

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
_When an issue has been solved and tested by the developer, an pull request must be submitted in the repository for validation. This is so the branch can be merged with the master branch. The Merge Request must follow the rules given below._
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
