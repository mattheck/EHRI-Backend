# -*- coding: utf-8 -*-

import logging
import json
import requests
import jwt
from fhirclient import client
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest

from flask import Flask, request, redirect, session

# app setup
smart_defaults = {
    'app_id': '31a0fdc8-3fae-463d-8cfe-2c406d98a820',
    'api_base': 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/',
    'redirect_uri': 'http://localhost:8000/fhir-app',
}

app = Flask(__name__)


def _save_state(state):
    session['state'] = state


def _get_smart():
    state = session.get('state')
    if state:
        return client.FHIRClient(state=state, save_func=_save_state)
    else:
        return client.FHIRClient(settings=smart_defaults, save_func=_save_state)


def _logout():
    if 'state' in session:
        smart = _get_smart()
        smart.reset_patient()


def _reset():
    if 'state' in session:
        del session['state']


def _get_prescriptions(smart):
    bundle = MedicationRequest.where(
        {'patient': smart.patient_id}).perform(smart.server)
    pres = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
    if pres is not None and len(pres) > 0:
        return pres
    return None


def _get_medication_by_ref(ref, smart):
    med_id = ref.split("/")[1]
    return Medication.read(med_id, smart.server).code


def _med_name(med):
    if med.coding:
        name = next((coding.display for coding in med.coding if coding.system ==
                    'http://www.nlm.nih.gov/research/umls/rxnorm'), None)
        if name:
            return name
    if med.text and med.text:
        return med.text
    return "Unnamed Medication(TM)"


def _get_med_name(prescription, client=None):
    if prescription.medicationCodeableConcept is not None:
        med = prescription.medicationCodeableConcept
        return _med_name(med)
    elif prescription.medicationReference is not None and client is not None:
        med = _get_medication_by_ref(
            prescription.medicationReference.reference, client)
        return _med_name(med)
    else:
        return 'Error: medication not found'


def get_fhir_record():
    """
    Retrieve OAuth2.0 token using Client Credentials Grant.

    Args:
        - client_id (str): Client ID from OAuth2.0 provider.
        - client_secret (str): Client Secret from OAuth2.0 provider.
        - token_url (str): OAuth2.0 provider's token endpoint URL.
        - scope (list or str, optional): Scope(s) for which the application requests access.

    Returns:
        dict: Contains access token and other details.
    """ 

    token = ''
    jwt_assertion = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ1cm46b2lkOmZoaXIiLCJjbGllbnRfaWQiOiIzMWEwZmRjOC0zZmFlLTQ2M2QtOGNmZS0yYzQwNmQ5OGE4MjAiLCJlcGljLmVjaSI6InVybjplcGljOk9wZW4uRXBpYy1jdXJyZW50IiwiZXBpYy5tZXRhZGF0YSI6IlkxTDV3X0xpYlp4MWdRTlIweDItZ1VEb2dWcEdWLVNaTUpLNFBVUG5qWXp6UDhTb2dIdGI5NkpSODBfZFhZcHhUOUVrVVJ4c1l5dVA5SFdObm5oLTNCUVlRYzA0bVZXOTY2VjNjdUJyS2RsVmhMczI0SEpoaVJjcGt5eHk3STNoIiwiZXBpYy50b2tlbnR5cGUiOiJhY2Nlc3MiLCJleHAiOjE2OTIyMDI3MjIsImlhdCI6MTY5MjE5OTEyMiwiaXNzIjoidXJuOm9pZDpmaGlyIiwianRpIjoiYzYxOGIyMGEtYmY5Yy00YTYzLWE1MWUtMzc5MDJlOTNhYmJkIiwibmJmIjoxNjkyMTk5MTIyLCJzdWIiOiJldk5wLUtoWXdPT3FBWm4xcFoyZW51QTMifQ.Ns_vdGvQye5bIyT1qYJRc2DFh5ki0PgezVC_R6DDoHCayYdanH1V0GVA4N_pE6vnvCyCI8AA3t630ub12r-K0JpQBBLJ2G6X-wMqi4HJrbPi5VSAuvtdIsSfsOKaDNAUyExI6LTY9Orpj8cX-xzR56SH7AYO94s8h7sEbWGD79f1-dwh8Rsw84IeHf0nvbeKMFG_mbjlH7hylHiC5KQUs0EkbycI3AgSTO0JhdKpj0JngkS-KbN9o1DXXMlw_eEty8z9qDWXtZ__MeQOADE61olMEwCRJbUOeCWdmXeBTRH2vwwGLvRD-xg5IbUIde4Us0GFew-AnPbcYYb9c0fheQ"

    auth_url = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth_data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_assertion 
    }

    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)

    # Printing the response for debugging
    print(auth_response.status_code)
    print(auth_response.text)

    token_response = auth_response.json()
    print(token_response)
    if 'access_token' not in token_response:
        raise ValueError(f"Failed to obtain access token: {token_response.get('error_description')}")
    else: 
        token = "Bearer"+token_response.access_token

    fhir_url = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/"
    fhir_headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    fhir_data = {}

    fhir_response = requests.post(fhir_url, headers=fhir_headers, data=fhir_data)

# Printing the response for debugging
    print(fhir_response.status_code)
    print(fhir_response.text)

    return fhir_response
# views


@app.route('/')
@app.route('/index.html')
def index():
    return "Please hit the /api endpoint."


@ app.route('/fhir-app/')
def callback():
    """ OAuth2 callback interception.
    """
    smart = _get_smart()
    try:
        smart.handle_callback(request.url)
    except Exception as e:
        return """<h1>Authorization Error</h1><p>{0}</p><p><a href="/">Start over</a></p>""".format(e)
    return redirect('/')

@app.route('/api', methods=['GET', 'PUT', 'DELETE', 'POST'])
def _backend_client_route(patientId=1234):
   if request.method == 'GET':
        # try:
            return get_fhir_record()
        # except Exception as e:
            # return "Authorization Error. Please start over.".format(e)
   elif request.method == "PUT":
       return 'PUT method not supported.'
   elif request.method == "DELETE":
       return 'DELETE method not supported.'
   elif request.method == "POST":
       return 'POST method not supported.'


@ app.route('/logout')
def logout():
    _logout()
    return redirect('/')


@ app.route('/reset')
def reset():
    _reset()
    return redirect('/')


# start the app
if '__main__' == __name__:
    import flaskbeaker
    flaskbeaker.FlaskBeaker.setup_app(app)

    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, port=8000)
