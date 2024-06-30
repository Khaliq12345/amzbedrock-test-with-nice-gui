from nicegui import ui, app
import ultraimport
from descriptions import *

dashboard = ultraimport('pages/dashboard.py')
ph = ultraimport('pages/pageHelpers.py')

def paidDashboard():
    dashboard.header()
    with ui.element('body').classes('desktop bg-black'):
        with ui.row().classes('w-full bg-white'):
            with ui.row().classes('w-full justify-center m-2'):
                for i in range(len(long_module_names)):
                    with ui.column().classes('col-4'):
                        with ui.card(align_items='center').classes('w-full shadow-up-3'):
                            with ui.card_section():
                                ui.label(f"Grouped {long_module_names[i]}").classes('text-h5 text-primary')
                                ui.label(f"Grouped {module_descriptions[i]}").classes('text-subtitle2')
                            ui.separator()
                            with ui.card_actions():
                                with ui.link(target=f'/group/module{i+1}'):
                                    ui.button(f"Use this module {i+1}").props('push color="primary"').classes('shadow-up-2')
                            
def index():
    if app.storage.user.get('user'):
        if app.storage.user['user']['is_paid']:
            paidDashboard()
        else:
            dashboard.freeDashboard()
    else:
        dashboard.freeDashboard()

def engine():
    if ph.is_still_login():
        index()
    else:
        ui.navigate.to('/login')