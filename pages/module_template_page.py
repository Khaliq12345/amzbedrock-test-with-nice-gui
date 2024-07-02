import pandas as pd
from nicegui import ui, events, app
from io import BytesIO
import helpers as hep
from descriptions import *
from campaign_names import *
import io
import pages.pageHelpers as ph
import asyncio

class ModuleTemp:
    def __init__(self, module_name: str, module_description: str, module_obj, cno: dict):
        self.CAMPAIGN_NAME_ORDER = cno
        self.module_name = module_name
        self.module_description = module_description
        self.module_obj = module_obj
        
        self.input_df = None
        self.output_data = None
        self.errors = {"error_messages": [], "warning_messages": []}
    
    async def data_processing(self, module, input_df, name_values):
        await asyncio.sleep(3)
        #try:
        output_data = module(input_df, name_values)
        return output_data
        # except Exception as e:
        #     self.spinner_col.clear()
        #     ui.notification(f"""
        #     Error while processing the module. 
        #     {e}
        #     """, position='top', multi_line=True, type='negative', timeout=10, close_button=True)

    async def data_checking(self):
        try:
            self.errors = self.module_obj.error_check(self.input_df)
        except Exception as e:
            ui.notification(f"""
            Error while processing the module. 
            {e}
            """, position='top', multi_line=True, type='negative', timeout=10, close_button=True)
            
    def handle_errors(self, err_color: str):
        if len(self.errors['error_messages']) > 0:
            self.start_button.disable()
            self.proceed_anyway_button.disable()
        elif len(self.errors['warning_messages']) > 0:
            self.start_button.disable()
        with self.error_data_col:
            with ui.expansion(caption="Show errors").props(f'header-class="bg-{err_color}-3"').classes('w-full border rounded-borders'):
                for x in self.errors['warning_messages']:
                    ui.markdown(f'ℹ️ <span style="color: orange;">**Info:** {x}</span>').classes('w-full')
                for x in self.errors['error_messages']:
                    ui.markdown(f'⚠️ <span style="color: red;">**Danger:** {x}</span>').classes('w-full')
    
    def handle_user_input(self, input_color: str):
      with self.input_data_col:
            if not self.input_df.empty:
                pass
            else:
                self.input_df = pd.DataFrame()
            with ui.expansion(caption="Show input data").props(
                f'header-class="bg-{input_color}-3"').classes('w-full rounded-borders'):
                ui.table.from_pandas(df=self.input_df.head()).classes(
                'w-full my-sticky-header-column-table').props('separator="cell" flat bordered')
    
    async def handle_upload(self, e: events.UploadEventArguments):
        self.input_data_col.clear()
        self.error_data_col.clear()
        self.output_data_col.clear()
        value = e.content.read()
        self.input_df = pd.read_excel(BytesIO(value))
        self.input_df = hep.clean_check_input_file(self.input_df)
        await self.data_checking()
        self.handle_user_input('blue')
        self.handle_errors('red')
  
    async def start_processing(self):
        name_values = [self.CAMPAIGN_NAME_ORDER[v] for v in self.campaign_name_order.value]
        if len(name_values) != len(list(self.CAMPAIGN_NAME_ORDER.keys())):
            name_values = list(self.CAMPAIGN_NAME_ORDER.values())
        #---------------------------------------------------------
        self.output_data_col.clear()
        self.spinner_col.clear()
        with self.spinner_col:
            ui.spinner(size='lg', type='dots')
        #---------------------------------------------------
        #try:
        with self.output_data_col:
            if self.input_df is not None:
                self.output_data = await self.data_processing(self.module_obj.proccess_df, self.input_df, name_values)
                with ui.expansion(caption="Show output").props('header-class="bg-green-3"').classes('w-full'):
                    ui.table.from_pandas(df=self.output_data.head(10)).classes(
                    'w-full my-sticky-header-column-table').props('separator="cell" flat bordered')
                    self.buffer = io.BytesIO()
                    writer = pd.ExcelWriter(self.buffer, engine='xlsxwriter')
                    self.output_data.to_excel(writer, sheet_name='Sheet1', index=False)
                    writer.close()
                with ui.column(align_items='center').classes('w-full px-10'):
                    ui.button("Download", on_click=lambda: ui.download(
                    self.buffer.getvalue(), f"Output_{app.storage.user['user']['username']}_result.xlsx", 'application/vnd.ms-excel'))
        # except Exception as e:
        #     self.spinner_col.clear()
        #     ui.notification(f"""
        #     Error while processing the module. 
        #     {e}
        #     """, position='top', multi_line=True, type='negative', timeout=10, close_button=True)
        self.spinner_col.clear()
        
    def on_click_menu(self):
        self.drawer_col.toggle()
        
    def drawer(self):
        with ui.drawer('left', bordered=True, elevated=True).classes('bg-grey-9 text-white').props('width=350 breakpoint="500"') as self.drawer_col:
            with ui.column().classes():
                with ui.row().classes('justify-center w-full'):
                    with ui.expansion('SINGLE PRODUCT ADS'):
                        for num, mod in enumerate(module_short_names):        
                            ui.separator()
                            with ui.link(target=f'/single/module{num+1}'):
                                ui.button(mod).props('size="12px" flat')
                            ui.space()
                    with ui.expansion('GROUP PRODUCT ADS'):
                        for num, mod in enumerate(module_short_names):        
                            ui.separator()
                            with ui.link(target=f'/group/module{num+1}'):
                                ui.button(f'Grouped {mod}').props('size="12px" flat')
                            ui.space()
    
    def on_logout(self):
        app.storage.user['auth'] = None
        app.storage.user['user'] = None
        ui.navigate.reload()
    
    def header(self):
        with ui.header(bordered=True):
            with ui.row().classes('w-full justify-between'):
                with ui.column():
                    ui.button(icon='menu', on_click=self.on_click_menu).props('push color="grey-9"')
                with ui.column():
                    ui.label(self.module_name).classes('w-full text-h4 text-weight-bold px-10 text-white')
                with ui.column():
                    ui.button(icon='logout', on_click=self.on_logout).props('push color="grey-9"')
           
    def page_template(self):
        self.drawer()
        self.header()
        with ui.column().classes('w-full px-10 mt-5'):
            with ui.expansion(caption="Description and Instruction").classes(
            'w-full').props('header-class="bg-grey-3" rounded-borders'):
                ui.markdown(self.module_description)

            self.campaign_name_order = ui.select(options=self.CAMPAIGN_NAME_ORDER, multiple=True,
            label="Set your campaign name order").classes('w-full q-mb-md').props('use-chips')

            ui.upload(label="Upload your excel file", on_upload=self.handle_upload, 
            auto_upload=True).classes('w-full h-20').props('flat no-border color="grey-9"')
            #---------------------------------------------------------------------------------------
            with ui.row().classes('justify-between w-full mt-5'):
                self.start_button = ui.button("Start Processing!", 
                on_click=self.start_processing).props('push')
                self.clear_button = ui.button("Clear!", 
                on_click=lambda: ui.navigate.reload()).props('push color="grey-9"')
                self.proceed_anyway_button = ui.button("Proceed Anyway!", 
                on_click=self.start_processing).props('push')
                ui.separator().props('color="black"')
            #---------------------------------------------------------------------------------------------------
            self.spinner_col = ui.column(align_items='center').classes('w-full justify-center mt-3')
                
            #self.input_error_ui(self.input_df, self.errors)
            self.input_data_col = ui.column().classes('w-full px-10 rounded-borders')
            self.error_data_col = ui.column().classes('w-full px-10 rounded-borders')
            self.output_data_col = ui.column().classes('w-full px-10 rounded-borders')
        
    def engine(self):
        if ph.is_still_login():
            self.page_template()
        else:
            ui.navigate.to('/single')
            

