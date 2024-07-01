from single import module_one, module_two, module_three, module_four, module_five, module_six, module_seven, module_eight
from group import g_module_eight, g_module_one, g_module_two, g_module_three, g_module_four, g_module_five, g_module_six, g_module_seven
from pages.module_template_page import ModuleTemp
from descriptions import *
from campaign_names import *
from nicegui import ui
from pages.loginPage import Login
from pages.signupPage import SignIn
from pages import single_pa, group_pa

#features to add:
#forget password, email reset, password reset, email verification before accessing data, validate form, add signup link and login link in each forms
#add logout button, edit error messages, make upload async, remove duplicate code from the modules, connect the cno_module to where it is needed

@ui.page('/single/module1')
def module_1_page():        
    mod = ModuleTemp("Sponsored Products Auto Targeting", module_1_text, module_one, single_cno_module_1)
    mod.engine()

@ui.page('/single/module2')
def module_2_page():         
    mod = ModuleTemp("Sponsored Products Manual Keyword Targeting", module_2_text, module_two, single_cno_module_2)
    mod.engine()
    
@ui.page('/single/module3')
def module_3_page():         
    mod = ModuleTemp("Sponsored Products ASIN Product Targeting", module_3_text, module_three, single_cno_module_3)
    mod.engine()
    
@ui.page('/single/module4')
def module_4_page():         
    mod = ModuleTemp("Sponsored Products Category Product Targeting", module_4_text, module_four, single_cno_module_4)
    mod.engine()
    
@ui.page('/single/module5')
def module_5_page():         
    mod = ModuleTemp("Sponsored Display Contextual ASIN Targeting", module_5_text, module_five, single_cno_module_5)
    mod.engine()

@ui.page('/single/module6')
def module_6_page():         
    mod = ModuleTemp("Sponsored Display Contextual Category Targeting", module_6_text, module_six, single_cno_module_6)
    mod.engine()

@ui.page('/single/module7')
def module_7_page():         
    mod = ModuleTemp("Sponsored Display Audience Catalog Targeting", module_7_text, module_seven, single_cno_module_7_8)
    mod.engine()
    
@ui.page('/single/module8')
def module_8_page():         
    mod = ModuleTemp("Sponsored Display Audience Category Targeting", module_8_text, module_eight, single_cno_module_7_8)
    mod.engine()
    
#--------------------------------------------------------------------------

@ui.page('/group/module1')
def group_module_1_page():        
    mod = ModuleTemp("Grouped Sponsored Products Auto Targeting", module_1_text, g_module_one, group_cno_module_1)
    mod.engine()

@ui.page('/group/module2')
def group_module_2_page():        
    mod = ModuleTemp("Grouped Sponsored Products Manual Keyword Targeting", module_2_text, g_module_two, group_cno_module_2)
    mod.engine()
    
@ui.page('/group/module3')
def group_module_3_page():        
    mod = ModuleTemp("Grouped Sponsored Products ASIN Product Targeting", module_3_text, g_module_three, group_cno_module_3)
    mod.engine()

@ui.page('/group/module4')
def group_module_4_page():       
    mod = ModuleTemp("Grouped Sponsored Products Category Product Targeting", module_4_text, g_module_four, group_cno_module_4)
    mod.engine()

@ui.page('/group/module5')
def group_module_5_page():       
    mod = ModuleTemp("Grouped Sponsored Display Contextual ASIN Targeting", module_5_text, g_module_five, group_cno_module_5)
    mod.engine()

@ui.page('/group/module6')
def group_module_6_page():       
    mod = ModuleTemp("Grouped Sponsored Display Contextual Category Targeting", module_6_text, g_module_six, group_cno_module_6)
    mod.engine()

@ui.page('/group/module7')
def group_module_7_page():       
    mod = ModuleTemp("Grouped Sponsored Display Audience Catalog Targeting", module_7_text, g_module_seven, group_cno_module_7_8)
    mod.engine()
    
@ui.page('/group/module8')
def group_module_8_page():       
    mod = ModuleTemp("Grouped Sponsored Display Audience Category Targeting", module_8_text, g_module_eight, group_cno_module_7_8)
    mod.engine()
    
#--------------------------------------------------------------------------------
    
@ui.page('/login')
def lpage():
    lp = Login()
    lp.engine()
    
@ui.page('/signup')
def signup_page():
    sp = SignIn()
    sp.engine()
    
@ui.page('/single')
def single_product_ad():
    single_pa.engine()
    
@ui.page('/group')
def group_product_ad():
    group_pa.engine()

ui.run(port=6100, title="AMZBEDROCK", storage_secret='amzbedrock', reconnect_timeout=60)