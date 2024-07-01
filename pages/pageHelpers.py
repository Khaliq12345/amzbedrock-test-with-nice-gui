from nicegui import ui, app
from dateparser import parse
import requests
import base64
import ultraimport
from pydantic import BaseModel, ValidationError, model_validator

FIREBASE_HOST = ultraimport('./config.py', 'FIREBASE_HOST')

class UserModel(BaseModel):
    username: str
    password1: str
    password2: str 
    firstname: str
    lastname: str
    email: str
    
    @model_validator(mode='after')
    def check_passwords_match(self):
        pw1 = self.password1
        pw2 = self.password2
        email = self.email
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        if '@' not in email:
            raise ValueError('email is not valid')
        if len(self.username) < 5:
            raise ValueError('username should be atleast 5 characters')

def get_user_info(email: str):
    encoded = email.encode()
    encoded = base64.b64encode(encoded).decode()
    url = f"https://{FIREBASE_HOST}/users/{encoded}.json"
    response = make_rest_req(None, None, url, method='get')
    return response

def is_still_login():
    print(app.storage.user.get('auth'), app.storage.user.get('user'))
    match app.storage.user.get('auth'):
        case None:
            return False
        case _:
            expiresIn = parse(app.storage.user['auth']['expiresIn'])
            if expiresIn > parse('now'):
                return True
            else:
                app.storage.user['auth'] = None
                app.storage.user['user'] = None
                return False

def make_rest_req(headers, json_data, url, method='post'):
    try:
        match method:
            case 'post':
                response = requests.post(url, headers=headers, json=json_data)
            case 'get':
                response = requests.get(url, headers=headers, json=json_data)
            case 'patch':
                response = requests.patch(url, headers=headers, json=json_data)
        if response.status_code == 200:
            return response.json()
        else:
            return False
    except:
        return False