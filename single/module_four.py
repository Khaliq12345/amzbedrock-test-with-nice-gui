import pandas as pd
from pydantic import field_validator, ValidationError
import helpers as hep
import ultraimport
cno_module_4 = ultraimport('__dir__/../campaign_names.py', 'single_cno_module_4')
out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_4_3_2_1')

def saving_module_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'category_file' in error['loc']:
        error_messages.append(f"Row {row.name} Categories File Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the category code in column A and category name in column B with no header row")
    elif 'negative_targeting' in error['loc']:
        error_messages.append(f"Row {row.name} Negative Targeting Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the ASINs in column A with no header row")

class Module4(hep.CommonObj):
    category_file: str
    negative_targeting: str | float
    
    @field_validator('category_file', mode='after')
    def validate_category_file(cls, input_data: str):
        df = hep.download_from_gdrive(input_data)
        if len(df.columns) != 2:
            raise ValueError
        return input_data
    
    @field_validator('negative_targeting', mode='after')
    def validate_negative_targeting(cls, input_data: str):
        if pd.isna(input_data):
            pass
        else:
            df = hep.download_from_gdrive(input_data)
            if len(df.columns) != 1:
                raise ValueError            
        return input_data

def error_check(input_data:pd.DataFrame):
    warning_messages = []
    error_messages = []
    for idx, row in input_data.iterrows():
        try:
            row_json = {
                'sku': row['SKU'],
                'asin': row['ASIN'],
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
                'category_file': row['Categories File'],
                'negative_targeting': row['Negative Targeting']
            }
            row_obj = Module4(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                saving_module_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }

@hep.add_ps_feature
def get_table(cols: list, neg_keywords: list = [], skus: list = []):
    items = []
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Campaign'
    })
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Ad Group'
    })
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Product Targeting'
    })
    for i in range(3):
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Bidding Adjustment"
        })
    for k in neg_keywords:
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Negative product targeting"
        })
    return items

def is_from_row(row, value, name):
    row_values = ['SKU', 'ASIN', 'Campaign Name Modifier', 'SKU Group Name']
    if value in row_values:
        return row[value]
    elif value == 'Category Name':
        return name
    else:
        return value

def make_campaign_name(row, campaign_name_order, name):
    campaign_name = ''
    i = 0
    while True:
        try:
            if i == 0:
                campaign_name += f"{is_from_row(row, campaign_name_order[i], name)}"
            else:
                campaign_name += f"_{is_from_row(row, campaign_name_order[i], name)}"
        except:
            break
        i += 1
    return campaign_name

def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_4):
    dfs = []
    for i, row in input_df.iterrows():
        cat_df = hep.download_from_gdrive(row['Categories File'])
        cat_names = cat_df[1].to_list()
        cat_ids = cat_df[0].to_list()
        for id_, name in zip(cat_ids, cat_names):
            if not pd.isna(row['Negative Targeting']):
                neg_kewords = hep.download_from_gdrive(row['Negative Targeting'])[0].to_list()
                x_table = get_table(out_cols, neg_keywords=neg_kewords)
            else:
                x_table = get_table(out_cols)
            #campaign name
            campaign_name = make_campaign_name(row, campaign_name_order, name)
            #operation
            x_table['Operation'] = 'create'
            x_table['Campaign ID'] = campaign_name
            x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
            x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = hep.parse_my_date(row['Start Date'])
            x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
            #state
            enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
            x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
            x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
            x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = 'enabled'
            
            x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
            console_sc_vc = lambda x, y, value: y if x == value else None
            x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
            x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
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
            x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = f'category="{id_}"'
            #adding negative asin
            if not pd.isna(row['Negative Targeting']):
                x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Campaign ID'] = campaign_name
                x_table.loc[x_table['Entity'] == 'Negative product targeting', 'State'] = 'enabled'
                x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Ad Group ID'] = campaign_name
                neg_kewords_asins = [f'asin="{neg}"' for neg in neg_kewords]
                x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Product Targeting Expression'] = neg_kewords_asins
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    output_dataframe['Keyword Text'] = output_dataframe['Keyword Text'].replace('nan', pd.NA)
    output_dataframe['Match Type'] = output_dataframe['Match Type'].replace('nan', pd.NA)
    return output_dataframe





