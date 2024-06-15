from multiprocessing import Manager, Queue
import module_1, module_2
from module_template_page import ModuleTemp
from descriptions import *
from campaign_names import *
from nicegui import ui

@ui.page('/module1')
def module_1_page():         
    mod = ModuleTemp("Sponsored Products Auto Targeting", module_1_text, module_1, cno_module_1)
    mod.page_template()

@ui.page('/module2')
def module_1_page():         
    mod = ModuleTemp("Sponsored Products Manual Keyword Targeting", module_2_text, module_2, cno_module_2)
    mod.page_template()

ui.run(port=4110)