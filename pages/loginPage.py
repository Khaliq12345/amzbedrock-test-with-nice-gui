from nicegui import ui, app
import ultraimport
from dateparser import parse
import pages.pageHelpers as ph
import asyncio

FIREBASE_WEB_API_KEY = ultraimport('./config.py', 'FIREBASE_WEB_API_KEY')
STRIPE_KEY = ultraimport('./config.py', 'STRIPE_KEY')
FIREBASE_HOST = ultraimport('./config.py', 'FIREBASE_HOST')

def is_email_verified(tokenId):
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'idToken': tokenId,
    }
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_WEB_API_KEY}'
    try:
        json_data = ph.make_rest_req(headers, json_data, url)
        if json_data['users'][0]['emailVerified']:
            return True
        else:
            return False
    except:
        return False

async def login_rest(email, password):
    await asyncio.sleep(3)
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'email': email,
        'password': password,
        'returnSecureToken': True,
    }
    url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}'
    json_data = ph.make_rest_req(headers, json_data, url)
    if json_data:
        email_verified = is_email_verified(json_data['idToken'])
        if email_verified:
            response = ph.get_user_info(email)
            if response:
                return {"localId": json_data['localId'], "email": json_data['email'],'idToken': json_data['idToken'], 
                        'expiresIn': parse("In 20 minutes").isoformat()}, response
        
class Login:
    email : ui.input
    password: ui.input
    
    async def on_login(self):
        with self.spinner_col:
            ui.spinner(size='lg', type='hourglass')
        logged_in =  await login_rest(self.email.value, self.password.value)
        if logged_in:
            app.storage.user['auth'] = logged_in[0]
            app.storage.user['user'] = logged_in[1]
            ui.notification("logged in", type='positive', 
                            on_dismiss=lambda: ui.navigate.to("/single"), timeout=2, close_button=True)
        else:
            ui.notification("Incorrect password or email", 
                            type='negative', timeout=2, close_button=True)
        self.spinner_col.clear()

    def login_page(self):
        ui.dark_mode(True)
        with ui.column(align_items='center').classes('w-full').style('gap: 5rem'):
            ui.space()
            with ui.card(align_items='center'):
                with ui.card_section():
                    with ui.column(align_items='center').classes('w-full').style('gap: 0.01rem'):
                        ui.icon("person", size="3em")
                        ui.label("Member Login").classes('text-h6')
                        self.spinner_col = ui.column()

                with ui.card_actions().props('vertical'):
                    with ui.column(align_items='stretch').classes('w-full').style('gap: 0.01rem'):
                        self.email = ui.input("Email").props('type=email')
                        self.password = ui.input("Password", password=True, password_toggle_button=True).props('type=password')
                with ui.column(align_items='center').classes('w-full'):
                    ui.button("Login", on_click=self.on_login).props('push')
    
    def engine(self):
        if ph.is_still_login():
            ui.navigate.to('/single')
        else:
            self.login_page()
                    
