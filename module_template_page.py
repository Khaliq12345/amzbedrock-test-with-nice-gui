import pandas as pd
from nicegui import ui, events, run
from io import StringIO, BytesIO
import helpers as hep
from descriptions import *
from campaign_names import *
import io

class ModuleTemp:
    def __init__(self, module_name: str, module_description: str, module_obj, cno: dict):
        self.CAMPAIGN_NAME_ORDER = cno
        self.module_name = module_name
        self.module_description = module_description
        self.module_obj = module_obj
        
        self.input_df = None
        self.output_data = None
        self.errors = {"error_messages": [], "warning_messages": []}
    
    @ui.refreshable
    def input_error_ui(self, input_df: pd.DataFrame|None, errors: list, input_color='grey', err_color='grey'):
        input_data_col = ui.column().classes('w-full')
        error_data_col = ui.column().classes('w-full')
        self.handle_errors(errors, error_data_col, err_color)
        with input_data_col:
            if input_df is not None:
                pass
            else:
                input_df = pd.DataFrame()
            with ui.expansion(caption="Show input data").props(f'header-class="bg-{input_color}-3"').classes('w-full px-10 rounded-borders'):
                ui.table.from_pandas(df=input_df.head()).classes('w-full my-sticky-header-column-table').props('separator="cell" flat bordered')
        
    def handle_errors(self, errors: dict, error_data_col: ui.column, err_color: str):
        if len(errors['error_messages']) > 0:
            self.start_button.disable()
            self.proceed_anyway_button.disable()
        elif len(errors['warning_messages']) > 0:
            self.start_button.disable()
        with error_data_col:
            with ui.expansion(caption="Show errors").props(f'header-class="bg-{err_color}-3"').classes('w-full px-10') as show_input_data:
                for x in errors['warning_messages']:
                    ui.markdown(f'ℹ️ <span style="color: orange;">**Info:** {x}</span>').classes('w-full')
                for x in errors['error_messages']:
                    ui.markdown(f'⚠️ <span style="color: red;">**Danger:** {x}</span>').classes('w-full')
    
    def handle_upload(self, e: events.UploadEventArguments):
        value = e.content.read()
        self.input_df = pd.read_excel(BytesIO(value))
        self.input_df = hep.clean_check_input_file(self.input_df)
        self.errors = self.module_obj.error_check(self.input_df)
        
    async def start_processing(self):
        name_values = [self.CAMPAIGN_NAME_ORDER[v] for v in self.campaign_name_order.value]
        if len(name_values) != len(list(self.CAMPAIGN_NAME_ORDER.keys())):
            name_values = list(self.CAMPAIGN_NAME_ORDER.values())
        #---------------------------------------------------------
        self.output_data_col.clear()
        self.spinner_col.clear()
        with self.spinner_col as spin:
            ui.spinner(size='lg', type='hourglass')
        #---------------------------------------------------
        with self.output_data_col:
            if self.input_df is not None:
                self.output_data = await run.cpu_bound(self.module_obj.proccess_df, self.input_df, name_values)
                with ui.expansion(caption="Show output").props('header-class="bg-green-3"').classes('w-full px-10'):
                    ui.table.from_pandas(df=self.output_data.head()).classes('w-full my-sticky-header-column-table').props('separator="cell" flat bordered')
                    self.buffer = io.BytesIO()
                    writer = pd.ExcelWriter(self.buffer.read(), engine='xlsxwriter')
                    self.output_data.to_excel(writer, sheet_name='Sheet1', index=False)
                    #writer.close()
                    ui.button("Download", on_click=lambda: ui.download(writer, 'result.xlsx', 'application/vnd.ms-excel'))
        self.spinner_col.clear()
        
    def on_click_menu(self):
        self.drawer_col.toggle()
        
    def drawer(self):
        with ui.drawer('left', bordered=True, elevated=True).classes('bg-grey-9 text-white').props('width=225 breakpoint="500"') as self.drawer_col:
            with ui.column(align_items='stretch'):
                ui.html('<div class="text-h7">ALL MODULES</div>')
                ui.separator()
                ui.button('Sponsored Products Auto Targeting').classes('shadow-up-5').props('push size="10px"').on_click(lambda: ui.navigate.to('/module1'))
                ui.space()
                ui.button('Sponsored Products Manual Keyword Targeting').classes('shadow-up-5').props('push size="10px"').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 3').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 4').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 5').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 6').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 7').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                ui.space()
                ui.button('Module 8').props('push size="10px"').classes('shadow-up-5').on_click(lambda: ui.navigate.to('/module2'))
                
    def page_template(self):
        self.drawer()
        with ui.column(wrap=True).classes('w-full'):   
            ui.button(icon='menu', on_click=self.on_click_menu).props('push color="grey-9"')
            ui.label(self.module_name).classes('w-full text-h5 text-weight-bold px-10')

            with ui.expansion(caption="Description and Instruction").classes('w-full px-10').props('header-class="bg-grey-3"') as expanded:
                ui.markdown(self.module_description)

            self.campaign_name_order = ui.select(options=self.CAMPAIGN_NAME_ORDER, multiple=True,
                                            label="Set your campaign name order").classes('w-full px-10').props('use-chips color="black"')

            ui.upload(label="Upload your excel file", on_upload=self.handle_upload, 
                                auto_upload=True).classes('w-full px-10 h-20').props('flat no-border color="grey-9"')
            
            self.spinner_col = ui.column().classes('w-full')    
            with ui.row(align_items='center').classes('w-full px-10') as submit_buttons:
                self.start_button = ui.button("Start Processing!", on_click=self.start_processing).classes('justify-center').props('push')
                ui.space()
                self.upload_button = ui.button("Upload!", 
                on_click=lambda: self.input_error_ui.refresh(self.input_df, self.errors, 'blue', 'red')).classes('justify-center').props('push color="grey-9"')
                ui.space()
                self.proceed_anyway_button = ui.button("Proceed Anyway!", on_click=self.start_processing).classes('push justify-center')
                
            self.input_error_ui(self.input_df, self.errors)
            self.output_data_col = ui.column().classes('w-full')

