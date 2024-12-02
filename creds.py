from google.oauth2.service_account import Credentials
import os

def login():
    """
    Login to access Google Sheets and Google Drive.
    Returns:
        creds: Credentials object.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(os.environ.get('GOOGLE_SERVICE_ACCOUNT'), scopes=SCOPES)
    return credentials
