from nicegui import ui, run
import ultraimport
from pages.pageHelpers import make_rest_req
import pages.pageHelpers as ph
import base64

FIREBASE_WEB_API_KEY = ultraimport('./config_things/config.py', 'FIREBASE_WEB_API_KEY')

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
    url = f"https://amzbedrock-ppc-tools-default-rtdb.firebaseio.com/users.json?auth={idToken}"
    response = ph.make_rest_req(headers, data, url, method='patch')
    if response:
        pass
    else:
        delete_created_user(idToken)
    return response

def heavy_compute(email, password, lname, fname, username):
    signedIn_message: dict = {"verification": False, 'idToken': None}
    signup_json = signup_rest(email, password)
    if signup_json:
        signup_token = signup_json['idToken']
        if verify_email(signup_token):
            signedIn_message['verification'] = True
            signedIn_message['idToken'] = signup_token
            if create_new_user(signup_token, email, lname, fname, username):
                pass
            else:
                ui.notification("Error creating user! Please try again", type='negative', timeout=2, close_button=True)
                return {"verification": False, 'idToken': None}
        else:
            signedIn_message['verification'] = False
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

def verify_email(tokenId: str):
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
        if self.password.value == self.confirm_password.value:
            with self.spinner_col:
                ui.spinner(size='lg', type='hourglass')
            self.signedIn_message = await run.cpu_bound(heavy_compute, 
            self.email.value, self.password.value, self.lname.value, self.fname.value, self.username.value)
            if self.signedIn_message:
                ui.notification("Verification email has been sent to your email, verify your account and login",
                            type='positive', close_button=True, on_dismiss=lambda: ui.navigate.to('/login'))
            else:
                ui.notify("Verification was not sent, check credentials and sign up again", type='negative', timeout=2, close_button=True)
            self.spinner_col.clear()
        else:
            ui.notification("Password doesn't match!", type='negative', timeout=2, close_button=True)
                 
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