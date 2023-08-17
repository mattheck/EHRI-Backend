# -*- coding: utf-8 -*-

import logging
import json
import datetime
import jwt
import uuid
import requests
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest

from flask import Flask, request, redirect, session

app_id = '31a0fdc8-3fae-463d-8cfe-2c406d98a820'
token_uri = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'

# app setup
smart_defaults = {
    'app_id': app_id,
    'api_base': 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/',
    'redirect_uri': 'http://localhost:8000/fhir-app',
}

app = Flask(__name__)

def get_fhir_record():
    """
    Retrieve OAuth2.0 token using Client Credentials Grant.

    Args:
        none
    Returns:
        dict: Contains access token and other details.
    """ 

    token = ''
    token_uri = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'
    fhir_uri = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/DSTU2/'

    with open("ehri-backend-private.pem", "r") as f:
        private_key = f.read()

    payload = {
        "iss": app_id,
        "sub": app_id,
        "aud": token_uri,
        "jti": str(uuid.uuid4()),
        # Expiry is set by adding a timedelta to the current time
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=4)
    }

    jwt_token = jwt.encode(payload, private_key, algorithm="RS512")
    print("Generated JWT:", jwt_token)

    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token 
    }

    auth_response =  requests.post(token_uri, headers=auth_headers, data=auth_data)

    # Printing the response for debugging
    print(f'Auth Response status code {auth_response.status_code}')
    print(f'Auth Response text {auth_response.text}')

    token_response = auth_response.json()
    
    if 'access_token' not in token_response:
        raise ValueError(f"Failed to obtain access token: {token_response.get('error_description')}")
    else:
        token = token_response.access_token
        print(f'access token {token}')
        token = "Bearer "+token

    print(f'token {token}')
    fhir_headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    fhir_data = {}

    fhir_response =  requests.post(fhir_uri, headers=fhir_headers, data=fhir_data)

# Printing the response for debugging
    print(f'FHIR Response status code {fhir_response.status_code}')
    print(f'FHIR Response text {fhir_response.text}')

    return fhir_response.text
# views

@app.route('/')
@app.route('/index.html')
def index():
    return "Please hit the /api endpoint."

@app.route('/api', methods=['GET', 'PUT', 'DELETE', 'POST'])
def _backend_client_route(patientId=1234):
   if request.method == 'GET':
        try:
            return get_fhir_record()
        except Exception as e:
            return "Authorization Error: {}. Please start over.".format(e)
   elif request.method == "PUT":
       return 'PUT method not supported.'
   elif request.method == "DELETE":
       return 'DELETE method not supported.'
   elif request.method == "POST":
       return 'POST method not supported.'


@app.route('/logout')
def logout():
    _logout()
    return redirect('/')


@app.route('/reset')
def reset():
    _reset()
    return redirect('/')


# start the app
if '__main__' == __name__:
    import flaskbeaker
    flaskbeaker.FlaskBeaker.setup_app(app)

    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)
