# -*- coding: utf-8 -*-

import logging
from ehri_key import load_private_key
import datetime
import jwt
import uuid
import requests
from flask import Flask, request

# Constants
app_id = '31a0fdc8-3fae-463d-8cfe-2c406d98a820'
token_uri = 'https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token'
fhir_uri = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/DSTU2/'
query = 'Patient/T1wI5bk8n1YVgvWk9D05BmRV0Pi3ECImNSK8DKyKltsMB'

# Timeout constant for requests
REQUEST_TIMEOUT = 10

app = Flask(__name__)

def generate_jwt_token(private_key):
    """Generate JWT token for authentication."""
    payload = {
        "iss": app_id,
        "sub": app_id,
        "aud": token_uri,
        "jti": str(uuid.uuid4()),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=4)
    }
    return jwt.encode(payload, private_key, algorithm="RS512")

def get_auth_token(jwt_token):
    """Retrieve the authentication token."""
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token 
    }
    logging.debug("Fetching auth token...")
    response = requests.post(token_uri, headers=auth_headers, data=auth_data, timeout=REQUEST_TIMEOUT)
    logging.debug("Received auth token response")
    return response.json()

def get_fhir_record(query):
    """Retrieve OAuth2.0 token using Client Credentials Grant."""
    logging.debug("Reading private key...")
    private_key = load_private_key()
    logging.debug("Generating JWT token...")
    
    jwt_token = generate_jwt_token(private_key)
    logging.debug("Fetching authentication token...")
    
    token_response = get_auth_token(jwt_token)
    
    if 'access_token' not in token_response:
        raise ValueError(f"Failed to obtain access token: {token_response.get('error_description')}")
    
    token = "Bearer " + token_response['access_token']
    fhir_headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    combined_uri = fhir_uri + query
    logging.debug("Fetching FHIR record...")
    fhir_response = requests.get(combined_uri, headers=fhir_headers, timeout=REQUEST_TIMEOUT)
    logging.debug(f"Received FHIR record response {fhir_response.text}")
    return fhir_response.text

@app.route('/')
@app.route('/index.html')
def index():
    return "Please hit the /api endpoint."

@app.route('/api', methods=['GET'])
def api_route():
    # Get the 'query' parameter from the URL, default to the constant if not provided
    print(type(request.args))  # Check the type
    print(request.args)        # Print the value
    query_param = request.args.get('query', default=query)
    try:
        return get_fhir_record(query_param)
    except Exception as e:
        return f"Authorization Error: {e}. Please start over."


# Commenting out these until they're implemented
# @app.route('/logout')
# def logout():
#     _logout()
#     return redirect('/')

# @app.route('/reset')
# def reset():
#     _reset()
#     return redirect('/')

if __name__ == '__main__':
    # Assuming you need flaskbeaker for session management or some other purposes
    import flaskbeaker
    flaskbeaker.FlaskBeaker.setup_app(app)

    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)
