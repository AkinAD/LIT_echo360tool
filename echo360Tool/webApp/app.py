from flask import Flask, render_template, send_from_directory, request, redirect, url_for
import os,sys
from os.path import join, dirname, realpath
import requests
import pandas as pd
from requests.models import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from toHTML import HTML
from datetime import date

app = Flask(__name__)
app.config["DEBUG"] = True

# Upload folder
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static', 'files')
REPORTS_FOLDER = os.path.join(APP_ROOT, 'reports')

app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER
app.config['REPORTS_FOLDER'] =  REPORTS_FOLDER

# open an HTML file to show output in a browser
HTML_REPORT_FILE = 'Echo360Tool_report_{}.html'.format(date.today().strftime("%b-%d-%Y"))
# outputHtml = open(HTML_REPORT_FILE, 'w')

# constant keywords
BASE_URL = "https://echo360.ca"
REQUEST_OAUTH2ACCESS_TOKEN = BASE_URL + "/oauth2/access_token"

oauth = None
tokenObject = None

@app.route('/')
def index():
    return render_template('index.html')
    
    
# Get the uploaded files
@app.route("/receive_form", methods=['POST'])
def uploadFiles():
      # get the uploaded file
      uploaded_file = request.files['file']
      status = request.form.get("status")
      targetColumn = request.form.get("targetColumn")
      clinetId =  request.form.get('clientId')
      clinetSecret =  request.form.get('clientSecret')
      generateToken(client_id=clinetId, client_secret=clinetSecret)
      if uploaded_file.filename != '':
        #    set the file path
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
           # save the file
           uploaded_file.save(file_path)
           csv_in = pd.read_csv(file_path)
           doStatusChange(csv_in, targetColumn, status)
           # open both files
           reportFile = os.path.join(REPORTS_FOLDER, HTML_REPORT_FILE)
           with open(HTML_REPORT_FILE,'r') as firstfile, open(reportFile,'w') as secondfile:
                for line in firstfile:
                    # write content to second file
                    secondfile.write(line)
      return send_from_directory(app.config['REPORTS_FOLDER'], HTML_REPORT_FILE)

@app.route('/api', methods=['GET'])
def apiHome():
    return "<h5>Ech0 360 tool 💫 </h5><p>Made by Akin</p>"

def generateToken(client_id, client_secret ):
    try:
        auth = HTTPBasicAuth(client_id, client_secret)
        client = BackendApplicationClient(client_id=client_id)
        global oauth
        oauth = OAuth2Session(client=client)
        global tokenObject
        tokenObject = oauth.fetch_token(token_url=REQUEST_OAUTH2ACCESS_TOKEN, auth=auth)
        if len(tokenObject): # i guess? 
            return True
    except:
        raise Exception("Error during Auth")


def doStatusChange(csvin, targetColumn="Echo360 User ID", status="Active"): 
    """This is literally the same method as in  echo360CommandLineTool/echo360Cleaner.py BUT 
    i caould not figure out imports so i just copied and pasted the code into here
    """
    result_colors = {
        'Success':      'lime',
        'Failure':      'red',
        'Error':        'yellow',
        'InvalidUserStatusChange': 'red',
    }
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
    outputHtml = open(HTML_REPORT_FILE, 'w')


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

if (__name__ == "__main__"):
     app.run(port = 5000)