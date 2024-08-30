from django.shortcuts import render
import os
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from django.shortcuts import redirect, render
from django.conf import settings
from django.http import HttpResponse
from google.auth.transport import requests
from django.views.decorators.csrf import csrf_exempt
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests
import uuid
 

# Load client secrets from the JSON file you downloaded
GOOGLE_CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'https://b07a-175-143-107-237.ngrok-free.app/rest/v1/calendar/redirect/'


def store_uuid_in_session(request):
    # Generate a UUID and store it in the session
    request.session['uuid'] = str(uuid.uuid4())
    return HttpResponse(f"UUID stored in session: {request.session['uuid']}")

def google_calendar_init_view(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    # Generate the authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline', 
        include_granted_scopes='true'
    )

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Retrieve the state from session data
    state = request.session.get('state')
    print("session before:", state)

    # Save the state in the session
    request.session['state'] = state
    request.session.save()

    # Debug: Print session after saving state
    print("Session after saving state: ", state)

    # Redirect to Google's OAuth 2.0 authorization page
    return redirect(authorization_url)


def google_calendar_redirect_view(request):

    # Retrieve the state from session data
    state = request.GET.get('state')
    print("session after:", state)

    if not state:
        return HttpResponse("Error: 'state' parameter is missing from the session.", status=400)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI

    # Use the authorization response to fetch the token
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials

    # Save the credentials for later use
    request.session['credentials'] = credentials_to_dict(credentials)

    return redirect('get_calendar_events')


def get_calendar_events_view(request):
    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])

    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    # Call the Google Calendar API to fetch events
    events_result = service.events().list(calendarId='8aaeb1c9e7883513ee537a4f4276fe951a317d9d45d61bd13ddd8e7c35598ce0@group.calendar.google.com', maxResults=10, singleEvents = True).execute()
    events = events_result.get('items', [])

    # Display the events
    return render(request, 'testapp1/events.html', {'events': events})

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

@csrf_exempt
def google_calendar_webhook(request):
    if request.method == 'POST':
        print("request:", request)
        # Log the entire request to debug
        print("Request Headers:", request.headers)            
        print("Request Body:", request.body)
        try:
            # Get the raw body data
            body = request.data
            print("request body:", body)
            # Ensure the body is not empty
            if not body:
                return HttpResponse("No data received.", status=400)
            # Parse the JSON data
            data = json.loads(body)
            # Process the JSON data
            print("Webhook notification received:", data)
            # Respond to acknowledge receipt
            return HttpResponse("Notification received.", status=200)
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return HttpResponse(f"Error: {e}", status=400)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return HttpResponse(f"Error: {e}", status=500)
    else:
        return HttpResponse("Invalid request method.", status=405)

def start_watch(request):
    credentials_info = request.session.get('credentials')
    credentials = Credentials(**credentials_info)
    service = build('calendar', 'v3', credentials=credentials)
    request.session['uuid'] = str(uuid.uuid4())

    request_body = {
        'id': request.session['uuid'],  # Unique identifier for this channel
        'type': 'web_hook',
        'address': 'https://b07a-175-143-107-237.ngrok-free.app/google_calendar_webhook/',
    }
 
    response = service.events().watch(calendarId='8aaeb1c9e7883513ee537a4f4276fe951a317d9d45d61bd13ddd8e7c35598ce0@group.calendar.google.com', body=request_body).execute()
    print('Watch response:', response)
    # {'kind': 'api#channel', 
    #  'id': '7cc35875-0124-4030-b5c8-fd157320bf75', 'resourceId': 'x4zwZ-SeBJLq1J2uWRINR5Uo294', 'resourceUri': 'https://www.googleapis.com/calendar/v3/calendars/8aaeb1c9e7883513ee537a4f4276fe951a317d9d45d61bd13ddd8e7c35598ce0%40group.calendar.google.com/events?alt=json', 'expiration': '1725594571000'}

    return HttpResponse('Webhook sukses')