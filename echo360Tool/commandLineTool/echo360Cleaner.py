import os
import re

import webbrowser
import pandas as pd

import requests
import click
import six
# CLI interface stuff
from PyInquirer import (Token, ValidationError, Validator, print_json, prompt,
                        style_from_dict)
from sendgrid.helpers.mail import *

from pyfiglet import figlet_format
try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None

try:
    from termcolor import colored
except ImportError:
    colored = None


# OAUTH2 stuff for generating echo360 access token
from requests.models import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

# generating an HTML file
from toHTML import HTML

style = style_from_dict({
    Token.QuestionMark: '#fac731 bold',
    Token.Answer: '#4688f1 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})

BASE_URL = "https://echo360.ca"
REQUEST_OAUTH2ACCESS_TOKEN = BASE_URL + "/oauth2/access_token"
bold_start = "\033[1m"
bold_end = "\033[0;0m"

oauth = None
tokenObject = None

# open an HTML file to show output in a browser
HTMLFILE = 'Echo360Tool_report.html'
outputHtml = open(HTMLFILE, 'w')

def echoGetRequest(path, params, ):
    """
    Honesyly, i made this for some reason but ended up going the lazy route and just using string building to make api requests
    """
    return oauth.get(path)

def log(string, color, font="slant", figlet=False):
    if colored:
        if not figlet:
            six.print_(colored(string, color))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color))
    else:
        six.print_(string)

class EmptyValidator(Validator):
    """Check if field marked as required was left blank
    """
    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="No no, bad human! You can't leave this field blank. Please enter a value",
                cursor_position=len(value.text))



class FilePathValidator(Validator):
    """ Check if inputted file pathis acceptable """
    def validate(self, value):
        if len(value.text):
            if os.path.isfile(value.text):
                return True
            else:
                raise ValidationError(
                    message="File not found",
                    cursor_position=len(value.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))
        
class APIValidator(Validator):
    def validate(self, value):
        if len(value.text):
            chunks = value.text.split()
            if(len(chunks) == 2):
                CLIENT_ID = chunks[0]
                CLIENT_SECRET = chunks[1]
                # https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow
                # With provided user client id and client secret, generate auth token and use during session
                try:

                    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
                    client = BackendApplicationClient(client_id=CLIENT_ID)
                    global oauth
                    oauth = OAuth2Session(client=client)
                    global tokenObject
                    tokenObject = oauth.fetch_token(token_url=REQUEST_OAUTH2ACCESS_TOKEN, auth=auth)
                    if len(tokenObject): # i guess? 
                        return True
                except:
                    raise ValidationError(
                        message="There is an error with your clientId and client secret!",
                        cursor_position=len(value.text))
            else:
                raise ValidationError(
                    message="Please enter your client ID first and then your Client secret sepereated by a single space",
                    cursor_position=len(value.text))

        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))

def askClientIDAndSecret():
    """Using the pyInquirer library, the following questions are triggered on the command line for user input
        See here https://github.com/CITGuru/PyInquirer 

    """
    questions = [
        {
            'type': 'input',
            'name': 'client_data',
            'message': 'Enter Echo360 clientID and clientSecret Key ( seperated by single space)',
            'validate': APIValidator,
        },
    ]
    answers = prompt(questions, style=style)
    return answers

def askFilterQuestions():
    """Using the pyInquirer library, the following questions are triggered on the command line for user input
        See here https://github.com/CITGuru/PyInquirer 

    """
    questions =[
        {
            'type': 'input',
            'name': 'csv_in',
            'message': 'Enter csv file path:',
            'validate': FilePathValidator,
            # 'filter': lambda val: open(val).read(),
        },
        {
            'type': 'confirm',
            'name': 'echoID_deactivate',
            'message': 'Skip filtering and set echoIds to inactive?',
            'default': False,
        },
        {
            'type': 'confirm',
            'name': 'guided',
            'message': 'Go through entire guided filtering?',
            'when': lambda answers: not answers['echoID_deactivate'],
            'default': False,
            
        },
         {
            'type': 'input',
            'name': 'commandList',
            'message': 'Enter Your prepopulated command list or enter # to generate template file for commands list',
            'when': lambda answers: not answers['echoID_deactivate'] and not answers['guided']
        },
        {
            'type': 'list',
            'name': 'email_filter',
            'message': 'Which emails are we looking for?',
            'choices': ['@my.yorku.ca|@yorku.ca', 'all others', 'N/A'],
            'when' : lambda answers:not answers['echoID_deactivate']
        },
        {
            'type': 'list',
            'name': 'duplicate_filter',
            'message': 'Show Duplicate or Unique users?',
            'choices': ['Duplicate', 'Unique', 'N/A'],
            'when' : lambda answers:not answers['echoID_deactivate']

        },
        {
            'type': 'list',
            'name': 'LMS_filter',
            'message': 'Show Moodle or Canvas users?',
            'choices': ['Moodle', 'Canvas', 'N/A'], #TODO: add filter to remove 'both' 
            'when' : lambda answers:not answers['echoID_deactivate']
        },
        {
            'type': 'list',
            'name': 'role_filter',
            'message': 'Which user roles do you want to see?',
            'choices': ['Student', 'Instructor', 'Admin', 'Scheduler', 'Anonymous', 'N/A'],
            'when' : lambda answers:not answers['echoID_deactivate']

        },
        {
            'type': 'list',
            'name': 'video_filter',
            'message': 'Care if the user has watched a video or not?',
            'choices': ['Watched Video', 'Did not watch', 'N/A'],
            'when' : lambda answers:not answers['echoID_deactivate']

        },
        {
            'type': 'list',
            'name': 'branch',
            'message': 'Output to a file or Run API delete on users?',
            'choices': ['File', 'API'],
            'when' : lambda answers:not answers['echoID_deactivate']


        },
        {
            'type': 'input',
            'name': 'branch_filename',
            'message': 'File name (do not add fille type suffix \'.csv\')',
            'when': lambda answers: not answers['echoID_deactivate'] and answers['branch'] == 'File'
        },
        {
            'type': 'confirm',
            'name': 'branch_api_start',
            'message': 'Do you have permission to do deactivate Echo users?',
            'when': lambda answers: answers['echoID_deactivate'] or answers['branch'] == 'API',
            'default': False,
        },
    ]

    answers = prompt(questions, style=style)
    return answers

def filterEmail(data, criteria):
    """Helper function to apply filtering to some input
       Citeria is to match the normalized email column (using regex) of output CSV file from ECHO360 support

       Returns:
       Pandas filtered data macth
    """
    # regex for string matching, na to ignore empty fields
    return data[data["Institution User Normalized Email"].str.contains(criteria, regex=True, na=False)]

def filterDuplicateorUnique(data, criteria):
    """Helper function to apply filtering to some input
       Citeria is to match the duplicate or unique column of output CSV file from ECHO360 support

       Returns:
       Pandas filtered data macth
    """
    return data[data["Duplicate or Unique?"] == criteria]

def filterMoodleOrCanvas(data, criteria):
    """Helper function to apply filtering to some input
       Citeria is to match the canvas  or moodle id column of output CSV file from ECHO360 support

       Returns:
       Pandas filtered data macth
    """
    return data[data["{} LMS ID".format(criteria)] != "None" ]
    
def filterUserRole(data, criteria):
    """Helper function to apply filtering to some input
       Citeria is to match the user role column of output CSV file from ECHO360 support

       Returns:
       Pandas filtered data macth
    """
    return data[data["Institution User Is {}".format(criteria)] == 1 ] # get all users whose role matches criteria i.e if user is a student, the field value will be = 1

def filterWatchedVideo(data, criteria):
    """Helper function to apply filtering to some input
       Citeria is to match the video column of output CSV file from ECHO360 support

       Returns:
       Pandas filtered data macth
    """
    return data[data["Either View Session or Video View"] == criteria]

def doFiltering(answers):
    """Takes the responses from the command line questions and applies filtering to CSV file
        Filters are based off functionality provided by pandas library

        Parameters:
        answer (json): Output of the command line questionare. this method is heavily dependent on the questionaire

        Returns:
        Filtered CSV file
    """
    csvin = pd.read_csv(answers['csv_in'])
    if (answers['email_filter'] == '@my.yorku.ca|@yorku.ca'):
       csvin = filterEmail(csvin, answers['email_filter'] )
    elif(answers['email_filter'] == 'all others'):
        csvin = csvin[not csvin["Institution User Normalized Email"].str.contains('@my.yorku.ca|@yorku.ca', regex=True)]  # FIXME: untested
    if(not answers['duplicate_filter']  == 'N/A'):
        csvin = filterDuplicateorUnique(csvin,  answers['duplicate_filter'])
    if(not answers['LMS_filter']  == 'N/A'):
        csvin = filterMoodleOrCanvas(csvin,  answers['LMS_filter'])
    if(not answers['role_filter']  == 'N/A'):
        csvin = filterUserRole(csvin,  answers['role_filter'])
    if(not answers['video_filter']  == 'N/A'):
        csvin = filterWatchedVideo(csvin,  answers['video_filter'])
    if(answers['branch']  == 'File'):
        csvin.to_csv("{}.csv".format(answers['branch_filename']))
    return csvin

# TODO: continue implementing, from here. check for error by apis error response, append to some list


def doStatusChange(csvin, targetColumn="Echo360 User ID",status="Inactive"):
    """Calls the Echo 360 Api and changes user status
        Writes actiosn completed to HTML file as well as temp json file
        
        HTML file contains table showing whether action was successful or resulted in an error. It also provides an undo link to undo a specific action (reactive or deactivate a given user)
            Undo link is only valid while user token is valid. (1 hour)


    Parameters:
    csvin (csv): Incoming CSV file with ECho360 ids in some column
    
    targetColumn (string): The row containing echoIds, ( or emails, or External ID or SSO ID) of the User to Disable / Enable. Defaults to "Echo360 User ID" 
    
    status (string): Can be either 'Active' or 'Inactive'. Defaults to'Inactive'


    Returns: 
    List of Strings: with Echo Ids and whether the operaton succeeded or not 
    """
    result_colors = {
        'Success':      'lime',
        'Failure':      'red',
        'Error':        'yellow',
        'InvalidUserStatusChange': 'red',
    }

    print("In do status change method")
    alteredIDs=[]
    header=['S/N','Echo360 User ID', 'Email', 'Old Status', 'Updated Status', 'Result', 'Undo Link']

    apiErrorResponse = {
  "error": "InvalidUserStatus",
  "message": "Invalid User status"
        }
    apiErrorResponse2 = {
            
    "error": "InvalidUserStatusChange",
    "message": "Invalid User status change"
        }
    count = 0
    tempJson = "tempResponse.json"
    yuh = open(tempJson, 'w')
    yuh.write("[")
    

    outputHtml.write("<h2>Howdy Human! Here's a report of your attempt to set the following users to {} </h2>".format(status))

    for index, row in csvin.iterrows():
        count = count +1
        if "Echo360 User ID" in csvin.columns:
            print("Echo row exists")
            print("=== Row ===")
            print(row)

            # Build the url and make a get request to alter the user status 
            # token is already defined gloablly and once a user provides theit echo360 client id and secret,
            # a new token is generated and stored to be used everywhere in the script
            print("=== request url ===")
            oppositeStatus = "Active" if status == "Inactive" else "Inactive"
            undoLink = "{}:443/public/api/v1/users/{}/status/{}?access_token={}".format(BASE_URL, row["Echo360 User ID"], oppositeStatus, tokenObject['access_token'])
            
            
            print("{}:443/public/api/v1/users/{}/status/{}?access_token={}".format(BASE_URL, row["Echo360 User ID"], status, tokenObject['access_token']))
            print("=== request response ===")
            # response = requests.get("{}:443/public/api/v1/users/{}/status/{}?access_token={}".format(BASE_URL, row[index]["Echo360 User ID"], status, tokenObject['access_token']))  # Broken
            response = requests.get("{}:443/public/api/v1/users/{}/status/{}?access_token={}".format(BASE_URL, row["Echo360 User ID"], status, tokenObject['access_token']))  # Working
            echoResponse = response.json()
            print()
            print(response.text)
            if 'error' in echoResponse:
                color= result_colors[echoResponse['error']]
                colored_result = HTML.TableCell(echoResponse['error'], bgcolor=color)
                alteredIDs.append([index+1, row["Echo360 User ID"], "==", status, status, colored_result, HTML.link("Undo Link", undoLink)])
            else:
               color= result_colors["Success"]
               colored_result = HTML.TableCell("Success", bgcolor=color)
               alteredIDs.append([index+1, row["Echo360 User ID"], echoResponse['email'], oppositeStatus,  status, colored_result, HTML.link("Undo Link", undoLink)])
            
            yuh.write(response.text)
            yuh.write(',')

        if count == len(csvin.index):

            htmlCode = HTML.table(alteredIDs, header_row=header)
            print(htmlCode)
            
            outputHtml.write(htmlCode)
            outputHtml.write('<p>')
            yuh.write(']')
            outputHtml.close()
            yuh.close()
            return outputHtml



@click.command()
def main():
    """
    Simple CLI for setting and filtering echo360 inactive accounts
    """
    log("Echo360 Cleaner", color="blue", figlet=True)
    log("Welcome to Akins Echo360 cleaner CLI", "green")
    # try:
    #     api_key = conf.get("api_key")
    # except KeyError:
        # api_key = askClientIDAndSecret()
        # conf.set(api_key)
    
    csv_in = None
    filters = askFilterQuestions()
    if ('echoID_deactivate' in filters and filters['echoID_deactivate']== False):
        csv_in = doFiltering(filters)
    else:
        csv_in = pd.read_csv(filters['csv_in'])
        print("Well, let the party begin")
    # print(filters)
    
    if 'branch' in filters and filters['branch'] == 'API' and filters['branch_api_start']== True:
        echoCred = askClientIDAndSecret()
        if (oauth != None and (not csv_in.empty or csv_in is not None)):
            doStatusChange(csv_in)
            
        else:
            print("Oauth failure of some kind . ¯\_(ツ)_/¯ beats me.")
        print(echoCred)
        # do API things here with filteredCSV
    elif 'echoID_deactivate' in filters and filters['echoID_deactivate'] == True and filters['branch_api_start']== True:
        #FIXME: ew, repeated code
        echoCred = askClientIDAndSecret()
        if (oauth != None and (not csv_in.empty or csv_in is not None)): 
            doStatusChange(csv_in)
            
        else:
            print("Oauth failure of some kind . ¯\_(ツ)_/¯ beats me.")
        print(echoCred)
    else:
        # Output to file 
        print("Output to file will live here ")

    # launch browser and show result
    webbrowser.open(HTMLFILE)
    # webbrowser.open(theJsonFile)



    

    # data = echoGetRequest(BASE_URL+"/public/api/v1/terms",params="")
    # print(data.json()["data"])
    
    # mailinfo = askEmailInformation()
    # if mailinfo.get("send", False):
    #     conf.set("from_email", mailinfo.get("from_email"))
    #     try:
    #         response = sendMail(mailinfo)
    #     except Exception as e:
    #         raise Exception("An error occured: %s" % (e))
        
    #     if response.status_code == 202:
    #         log("Mail sent successfully", "blue")
    #     else:
    #         log("An error while trying to send", "red")


if __name__ == '__main__':
    print("Starting ...")
    main()