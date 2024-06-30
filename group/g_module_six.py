import pandas as pd
import helpers as hep
from pydantic import ValidationError
import ultraimport
cno_module_6 = ultraimport('__dir__/../campaign_names.py', 'group_cno_module_6')
out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_5_6_7_8')
single = ultraimport('__dir__/../single/module_six.py')
        
class Module6(hep.GroupObj, single.Module6):
    pass
     
def error_check(input_data:pd.DataFrame):
    warning_messages = []
    error_messages = []
    for idx, row in input_data.iterrows():
        try:
            row_json = {
                'sku': 'Sample SKU',
                'asin': '0123456789',
                'sku_group_name': row['SKU Group Name'],
                'product_ads': row['Product Ads'],
                'portfolio_id': row['Portfolio ID'],
                'activate_campaign_and_ad_group': row['Activate Campaign and Ad Group'],
                'daily_budget': row['Daily Budget'],
                'bid_mod': row["Bid"],
                'console': row['Console'],
                'start_date': row['Start Date'],
                'bid_optimization': row['Bid Optimization'],
                'defense': row['Defense'],
                'contextual_targeting_file': row['Contextual Targeting Targeting File'],
            }
            row_obj = Module6(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                single.saving_module_errors(error, row, error_messages, warning_messages)
                hep.saving_group_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }
    
def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_6):
    dfs = []
    for i, row in input_df.iterrows():
        tc_df = hep.download_from_gdrive(row['Contextual Targeting Targeting File'])
        targetings, categories = tc_df[0].to_list(), tc_df[1].to_list()
        for cat, cat_name in zip(targetings, categories):
            x_table, pa_df = hep.make_the_table(row, single, out_cols)
            x_table.loc[:, 'Operation'] = 'create'
            #cost type
            cost_type_selector =  lambda x: "cpc" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else "vcpm"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
            #targeting expression
            targeting_exp_value = f'category="{cat}"'
            x_table.loc[x_table['Entity'] == 'Contextual Targeting', 'Targeting Expression'] = targeting_exp_value
            # #campaign name
            campaign_name = single.make_campaign_name(row, campaign_name_order, cat_name)
            
            x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00020'
            x_table.loc[:, 'Campaign Name'] = campaign_name  
            x_table.loc[:, 'Campaign ID'] = campaign_name
            x_table.loc[:, 'Portfolio ID'] = row['Portfolio ID']
            x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
            #date
            x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = hep.parse_my_date(row['Start Date'])
            #state
            enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
            x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
            x_table.loc[~(x_table['Entity'].isin(['Campaign', 'Ad Group'])), 'State'] = 'enabled'
            #Budget
            x_table.loc[x_table['Entity'] == 'Campaign', 'Budget Type'] = 'daily'
            x_table.loc[x_table['Entity'] == 'Campaign', 'Budget'] = row['Daily Budget']
            #sku and asin
            console_sc_vc = lambda x, y, value: y if x == value else None
            x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] =  console_sc_vc(row['Console'], pa_df[0].to_list(), 'SC') #pa_df[0].to_list()
            x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], pa_df[1].to_list(), 'VC') #pa_df[1].to_list()
            #Bid
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
            #Bid optimization
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Bid Optimization'] = row['Bid Optimization']
            dfs.append(x_table)
    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe


