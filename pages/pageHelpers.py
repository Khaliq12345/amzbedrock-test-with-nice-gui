from nicegui import ui, app
from dateparser import parse
import requests
import base64

def get_user_info(email):
    encoded = email.encode()
    encoded = base64.b64encode(encoded).decode()
    response = requests.get(f"https://amzbedrock-ppc-tools-default-rtdb.firebaseio.com/users/{encoded}.json")
    if response.status_code == 200:
        return response.json()
    else:
        return None

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