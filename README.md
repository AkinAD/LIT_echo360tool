# Lassonde IT ECHO360 clean up tool

This 'package' requires python3 ( as well as pip3). It is assumed from this point on that the end user has the appropriate python version.

Initial intended use case

```
- check for students who are enrolled in any course, be it current or past

- Make inactive

- make sure they are all 'students'  BUT leave the posibility to allow other types of roles

- find students that are not enrolled and don't have an @schulich.yorku.ca emails

- script needs it to write out an output file (csv) saying what it did

- add a roll back in case something happens?
- use ayden accunt as testing

- see if it is possible to pull past course data for a user

```

Final use case

- Package contains both a command line tool and a web app/ website for a GUI .
- Specific details about the CLItool and the Web app are discussed in their own sections

- Final use case is to upload/provide a CSV with ECHO360 User ID's present and the package makes requests to the Echo360 APi to chage their user status.

## Assumed Folder structure

```markdown
WhereEverOnYourDevice
├── echo360Tool/
│ ├── commandLineTool/
│ │ ├── **echo360Cleaner.py**
│ │ └──toHTML/
│ ├── webApp
| | ├── **app.py**
| | ├── reports/
| | ├── static/
| | ├── templates/
│ │ └──toHTML/
│ ├── requirements.txt
│ └── ...other things
```

## Dependencies

(some dependencies may be missing/ i may have forgotten to update this list)

- CLI tool

Create a file `requirements.txt` and place the following lines in the file

```txt
oauthlib==3.1.0
requests==2.23.0
requests-oauthlib==1.3.0

```

- Web app

```
flask
```

Run the following command in terminal from the same directory as the `reqirements.txt` file

```sh
 $ pip install -r requirements.txt
```

### Auth

To ensure this script is being used by the apparopriate parties, you will need to enter your unique echo360 **Client_ID** and **Client_Secret** on initialization. These can only be granted to echo360 accounts with admin priviledges. See the echo360 documentation for further details [Getting an Access Token using Swagger Docs](https://admin.echo360.com/hc/en-us/articles/360035034252-Generating-Client-Credentials-to-Obtain-Access-Token) .

# commandLineTool

Run the application with the following command. Ensure you are running the command from the directory the script is saved in.

```sh
# run directly
python echo360Cleaner.py

# OR run as 'executable'
chmod +x echo360Cleaner.py
./echo360Cleaner.py
```

OR run the script from the top level directory outside of the whole package

```sh
# run directly
python echo360Tool/commandLineTool/echo360Cleaner.py

# OR run as 'executable'
chmod +x echo360Tool/commandLineTool/echo360Cleaner.py
./echo360Tool/commandLineTool/echo360Cleaner.py
```

The CLI tool allows for both filtering and bulk deactivation of user accounts by echo Id's. The experience is relatively guided and can be altered if need be in the `/commandLineTool/echo360Cleaner.py` directory.

On complettion, an report is generated as an html file and is displayed in browser.

The `doStatusChange` method is the main chunk of the application. By default, Accounts are set to inactive and the target column is "Echo360 User ID" but this can be altered from in the code.

```python
def doStatusChange(csvin, targetColumn="Echo360 User ID",status="Inactive"):
    """Calls the Echo 360 Api and changes user status
        Writes actiosn completed to HTML file as well as temp json file
        ... """
```

# Web App

From outside the echo360Tool folder, run with the following command

```sh
python echo360Tool/webApp/app.py
```

The app should now be running at [http://127.0.0.1:5000/](http://127.0.0.1:5000/) . i.e localhost:5000

The Web app provides a single page form that allows users to uplad a CSV with echo360 ids and have the accounts be bulk activated/ deactivated. You are also able to specify which column of the csv the echo360 Id's are in by specifying the row header.

Just as inthe CLI tool, an HTML report is generated at the end to show the scucess/ failure of the tool.

### Results

| Status                      |                                    Meaning                                     |
| --------------------------- | :----------------------------------------------------------------------------: |
| **Success**                 | Recieved when all went well and the users status has been successfully changed |
| **InvalidUserStatusChange** |       indicates your request failed and nothing was changed with echo360       |
|                             |                                                                                |

A unique `undoLink` is provided beside every row of the results table. The link embeds your Client ID and Client secret with the users EchoID and a flipped status (i.e if you initially set users to Inactive, the link will have status as Active). When clicked, it makes a request to the ECHO30060 api and you are returned a json with the users Data, showing the user has been set to active. Int the event of a `InvalidUserStatusChange`, the undo Link will still work, setting the user to an opposite status.

## ===============================

**Generally, do not alter the folder or contents of `toHtml`. This is an external package and requires no modification**

## ===============================
