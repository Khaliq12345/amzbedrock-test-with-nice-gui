from nicegui import ui
import ultraimport
from pages.pageHelpers import make_rest_req
import pages.pageHelpers as ph
import base64
import asyncio

FIREBASE_WEB_API_KEY = ultraimport('./config.py', 'FIREBASE_WEB_API_KEY')
FIREBASE_HOST = ultraimport('./config.py', 'FIREBASE_HOST')

def validate_info(user_json):
    try:
        user = ph.UserModel(**user_json)
        print(user)
        return True
    except ph.ValidationError as e:
        errors = e.errors()
        for error in errors:
            error_message = error['msg'].split(',')[-1]
            if len(error['loc']) == 0:
                pass
            else:
                error_message = error_message.replace('Input', error['loc'][0])
            ui.notification(error_message, close_button=True, timeout=10, type='negative')

def delete_created_user(idToken):
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'idToken': idToken,
    }
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:delete?key={FIREBASE_WEB_API_KEY}'
    ph.make_rest_req(headers, json_data, url)

def create_new_user(idToken, email, lname, fname, username):
    headers = {
        'Content-Type': 'application/json',
    }
    encoded = email.encode()
    encoded_email = base64.b64encode(encoded).decode()
    data = {encoded_email: {"email": email, "is_paid": False,
                            'first_name': fname, 'last_name': lname, 'username': username}}
    url = f"https://{FIREBASE_HOST}/users.json?auth={idToken}"
    response = ph.make_rest_req(headers, data, url, method='patch')
    if response:
        pass
    else:
        delete_created_user(idToken)
    return response

async def process_signup_process(email, password1, password2, 
    lastname, firstname, username):
    await asyncio.sleep(3)
    signedIn_message: dict = {"verification": False, 'idToken': None}
    signup_json = signup_rest(email, password1)
    if signup_json:
        signup_token = signup_json['idToken']
        if send_email_verification(signup_token):
            print("Email verification sent")
            signedIn_message['verification'] = True
            signedIn_message['idToken'] = signup_token
            if create_new_user(signup_token, email, lastname, firstname, username):
                return signedIn_message

def signup_rest(email, password):
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'email': email,
        'password': password,
        'returnSecureToken': True,
    }
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}'
    return make_rest_req(headers, json_data, url)

def send_email_verification(tokenId: str):
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'requestType': 'VERIFY_EMAIL',
        'idToken': tokenId,
    }
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}'
    return make_rest_req(headers, json_data, url)

class SignIn:
    username: ui.input
    fname: ui.input
    lname: ui.input
    email: ui.input
    password: ui.input
    
    async def on_signup(self):
        user_json_info = {
            'username': self.username.value,
            'password1': self.password.value,
            'password2': self.confirm_password.value,
            'firstname': self.fname.value, 
            'lastname': self.lname.value,
            'email': self.email.value
        }
        if validate_info(user_json_info):
            with self.spinner_col:
                ui.spinner(size='lg', type='hourglass')
            self.signedIn_message = await process_signup_process(**user_json_info)
            if self.signedIn_message:
                ui.notification("Verification email has been sent to your email, verify your account and login",
                            type='positive', close_button=True, on_dismiss=lambda: ui.navigate.to('/login'))
            else:
                ui.notify("Sign up failed, check credentials and sign up again, maybe there is already an account with this email", 
                          type='negative', timeout=5, close_button=True)
            self.spinner_col.clear()
                 
    def signin_page(self):
        ui.dark_mode(True)
        with ui.column(align_items='center').classes('w-full').style('gap: 5rem'):
            ui.space()
            with ui.card(align_items='center'):
                with ui.card_section():
                    with ui.column(align_items='center').classes('w-full').style('gap: 0.01rem'):
                        ui.icon("person-add", size="3em")
                        ui.label("New member sign-up").classes('text-h6')
                        self.spinner_col = ui.column()

                with ui.card_actions().props('vertical'):
                    with ui.column(align_items='stretch').classes('w-full').style('gap: 0.01rem'):
                        self.email = ui.input("Email").props('type=email')
                        self.fname = ui.input("First name").props('type=text')
                        self.lname = ui.input("Last name").props('type=text')
                        self.username = ui.input("Username").props('type=text')
                        self.password = ui.input("Password", password=True, password_toggle_button=True).props('type=password')
                        self.confirm_password = ui.input("Confirm Password", password=True, password_toggle_button=True).props('type=password')
                with ui.column(align_items='center').classes('w-full'):
                    ui.button("Signup", on_click=self.on_signup).props('push')
    
    def engine(self):
        if ph.is_still_login():
            ui.navigate.to('/single')
        else:
            self.signin_page()