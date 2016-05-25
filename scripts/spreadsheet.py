import argparse
import os
import utils
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


global CONN
CONN = None

DEFAULT_CONFIG_DIR = './configs'
DEFAULT_SECRET_CLIENT_PATH = os.path.join(DEFAULT_CONFIG_DIR, 'client_secrets.json')
DEFAULT_USER_CREDENTIALS_PATH = os.path.join(DEFAULT_CONFIG_DIR, 'local_credentials.txt')


def connect(credentials_file=None, secret_client_config=None):
    # Reference: http://stackoverflow.com/questions/24419188/automating-pydrive-verification-process

    credentials_file = credentials_file or DEFAULT_USER_CREDENTIALS_PATH
    secret_client_config = secret_client_config or DEFAULT_SECRET_CLIENT_PATH

    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile(credentials_file or '')

    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
    # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()

    # Save the current credentials to a file
    gauth.SaveCredentialsFile(credentials_file)

    global CONN
    if not CONN:
        CONN = GoogleDrive(gauth)
    return CONN


def get_spreadsheet_by_id(file_id):
    connect()
    f = CONN.CreateFile({'id': file_id})
    f.FetchMetadata()
    return f


def iter_get_spreadsheet_content(f):
    connect()
    f.FetchContent(mimetype='text/csv')
    for i in f.content:
        yield i


def download_spreadsheet_to_file(f, local_file):
    connect()
    f.GetContentFile(local_file, mimetype='text/csv')


def upload_spreadsheet_from_file(local_file, f):
    connect()
    f.SetContentFile(local_file)
    f.Upload()


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--secret-client-file', dest='client_secret', default=None)
    parser.add_argument('-u', '--user-credentials-file', dest='user_credentials', default=None)
    args = parser.parse_args()

    utils.log('Trying to connect to google spreadsheets...')
    connect(credentials_file=args.client_secret, secret_client_config=args.user_credentials)
    utils.log('Connected and setup done!')
