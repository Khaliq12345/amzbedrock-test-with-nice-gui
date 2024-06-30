from nicegui import ui, app
from pages import pageHelpers as ph
import stripe
import base64
import asyncio
import ultraimport

STRIPE_KEY = ultraimport('./config_things/config.py', 'STRIPE_KEY')
FIREBASE_HOST = ultraimport('./config_things/config.py', 'FIREBASE_HOST')

async def verify_payment(email: str):
    await asyncio.sleep(10)
    stripe.api_key = STRIPE_KEY
    customer = stripe.Customer.search(query=f"email: '{email}'")
    if len(customer.data) == 1:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {"is_paid": True}
        encoded = email.encode()
        encoded = base64.b64encode(encoded).decode()
        url = f'https://{FIREBASE_HOST}/users/{encoded}.json'
        if ph.make_rest_req(headers, data, url, method='patch'):
            user_info = ph.get_user_info(email)
            return user_info
        else:
            ui.notification("Please use the paid button again. If you are not redirected kindly contact the support!", type='negative')
            return None
    else:
        ui.notification("Please subscribe before using the paid button", type='negative')
        return None

async def check_stripe():
    spin = ui.spinner()
    email = app.storage.user['user']['email']
    user_info = await verify_payment(email)
    if user_info:
        ui.navigate
        app.storage.user['user'] = user_info
        ui.navigate.reload()
    spin.visible = False
    # customer = stripe.Customer.search(query=f"email: '{email}'")
    # if len(customer.data) == 1:
    #     change_to_paid(email)
    # else:
    #     ui.notification("Please subscribe before using the paid button", type='warning')

def on_logout():
    app.storage.user['auth'] = None
    app.storage.user['user'] = None
    ui.navigate.reload()

def header():
    with ui.header().classes('text-black'):
        with ui.row().classes('w-full justify-between bg-white'):
            with ui.column(align_items='start').classes('col-5'):
                with ui.row(align_items='center').classes('w-full'):
                    with ui.column().classes('col-3'):
                        ui.icon('home', size='50px')
                    with ui.column(align_items='start').classes('col-7'):
                        with ui.tabs():
                            mod_one = ui.tab("Single Product Ads", icon='view_module').on('click', lambda: ui.navigate.to('/single'))
                            mod_two = ui.tab("Group Product Ads", icon='view_module').on('click', lambda: ui.navigate.to('/group'))
                            
            with ui.column(align_items='end').classes('col-5'):
                with ui.tabs() as tabs:
                    account_info = ui.tab("Account Info", icon='account_circle')
                    subscription_info = ui.tab("Subscription Info", icon='card_membership')
                    logout = ui.tab("Logout", icon='logout').on('click', on_logout)

def freeDashboard():
    ui.add_body_html("""
        <script async
        src="https://js.stripe.com/v3/buy-button.js">
        </script>""")
    header()
    with ui.row(align_items='center').classes('w-full justify-center p-5 mt-10 h-full'):
        with ui.card(align_items='center'):
            ui.html("""<stripe-buy-button
            buy-button-id="buy_btn_1PUOm3FkfOJ2ptxRPDPGVdLB"
            publishable-key="pk_test_51NJE4PFkfOJ2ptxR5FDICs6aQQ1B3gEhpit9jhhN1RFkjcngYyv2lB3H3YvsCc9dUXFM3kZg1CdjK1cFJh7LN9T000DMKbD433"
            >
            </stripe-buy-button>
            """)
            ui.button("Paid", on_click=check_stripe).classes('bg-black').props('push')
    with ui.footer(bordered=True).classes('bg-grey-9'):
        ui.row().classes('bg-white')

# def index():
#     if app.storage.user.get('user'):
#         if app.storage.user['user']['is_paid']:
#             paidDashboard()
#         else:
#             freeDashboard()
#     else:
#         freeDashboard()

# def engine():
#     if ph.is_still_login():
#         index()
#     else:
#         ui.navigate.to('/login')
    
# @ui.page('/dashboard')
# ui.run(port=2000)