import pandas as pd
import helpers as hep
from pydantic import ValidationError
import ultraimport
cno_module_1 = ultraimport('__dir__/../campaign_names.py', 'group_cno_module_1')
out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_4_3_2_1')
single = ultraimport('__dir__/../single/module_one.py')
        
class Module1(hep.GroupObj, single.Module1):
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
                'placement_product': row['Placement Product Page'],
                'placement_rest': row['Placement Rest Of Search'],
                'placement_top': row['Placement Top'],
                'daily_budget': row['Daily Budget'],
                'bid': row["Bid"],
                'bidding_strategy': row['Bidding Strategy'],
                'console': row['Console'],
                'start_date': row['Start Date'],
                'loose_match': row['loose-match'],
                'substitutes': row['substitutes'],
                'close_match': row['close-match'],
                'complements': row['complements'],
                'negative_url': row['Negative Targeting'],
            }
            row_obj = Module1(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                single.saving_module_errors(error, row, error_messages, warning_messages)
                hep.saving_group_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }
    
def make_the_table(row):
    neg_df, pa_df = None, None
    if not pd.isna(row['Negative Targeting']):
        neg_df = hep.download_from_gdrive(row['Negative Targeting'])
        neg_df_list = neg_df[0].to_list()
    else:
        neg_df_list = []
    if not pd.isna(row['Product Ads']):
        pa_df = hep.download_from_gdrive(row['Product Ads'])
        pad_df_list = pa_df[0].to_list()
    else:
        pa_df_list = []
    x_table = single.get_table(out_cols, neg_df_list, pad_df_list)
    return x_table, neg_df, pa_df

def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_1):
    dfs = []
    for i, row in input_df.iterrows():
        x_table, neg_df, pa_df = make_the_table(row)
        campaign_name = single.make_campaign_name(row, campaign_name_order)
        x_table.loc[:, 'Operation'] = 'create'
        x_table.loc[:, 'Campaign ID'] = campaign_name
        x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
        x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
        x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
        x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
        x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = hep.parse_my_date(row['Start Date'])
        x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Auto'
        enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
        x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
        x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
        targets = ['loose-match', 'close-match', 'complements', 'substitutes']
        x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = [enable_pause(row[t]) for t in targets]
        x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
        console_sc_vc = lambda x, y, value: y if x == value else None
        x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] =  console_sc_vc(row['Console'], pa_df[0].to_list(), 'SC') #pa_df[0].to_list()
        x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], pa_df[1].to_list(), 'VC') #pa_df[1].to_list()
        x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
        x_table.loc[x_table['Entity'].isin(['Campaign', 'Bidding Adjustment']), 'Bidding Strategy'] = row['Bidding Strategy']
        #Placement
        placement_values = ['Placement Product Page', 
                            'Placement Rest Of Search', 
                            'Placement Top']
        x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Placement'] = placement_values
        #Percentage
        perc_values = [
            row['Placement Product Page'],
            row['Placement Rest Of Search'],
            row['Placement Top']
        ]
        x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Percentage'] = perc_values
        x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = targets
        #adding negative keyword data
        if not pd.isna(row['Negative Targeting']):
            x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Campaign ID'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Negative Keyword', 'State'] = 'enabled'
            x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Keyword Text'] = neg_df[0].to_list()
            x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Match Type'] = neg_df[1].to_list()
        dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    output_dataframe['Keyword Text'] = output_dataframe['Keyword Text'].replace('nan', pd.NA)
    output_dataframe['Match Type'] = output_dataframe['Match Type'].replace('nan', pd.NA)
    return output_dataframe


