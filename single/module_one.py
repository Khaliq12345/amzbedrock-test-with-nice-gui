import pandas as pd
import helpers as hep
from pydantic import field_validator, ValidationError
import ultraimport
cno_module_1 = ultraimport('__dir__/../campaign_names.py', 'single_cno_module_1')

out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_4_3_2_1')

def saving_module_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'loose_match' in error['loc']:
        error_messages.append(f"Row {row.name} Loose-Match Error: Must be either yes or no")
    elif 'substitutes' in error['loc']:
        error_messages.append(f"Row {row.name} Substitutes Error: Must be either yes or no")
    elif 'close_match' in error['loc']:
        error_messages.append(f"Row {row.name} Close-Match Error: Must be either yes or no")
    elif 'complements' in error['loc']:
        error_messages.append(f"Row {row.name} Complements Error: Must be either yes or no")
    elif 'negative_url' in error['loc']:
        error_messages.append(f"Row {row.name} Negative Targeting Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the keyword in column A and match type in column B with no header row")

class Module1(hep.CommonObj):
    loose_match: str
    substitutes: str
    close_match: str
    complements: str
    negative_url: str | float
    
    @field_validator('loose_match', 'substitutes', 'close_match', 'complements', mode='after')
    def validate_yes_no(cls, input_data: str):
        if input_data in ["yes", "no"]:
            pass
        else:
            raise ValueError
        return input_data
    
    @field_validator('negative_url', mode='after')
    def validate_df(cls, input_data: str):
        if pd.isna(input_data):
            pass
        else:
            df = hep.download_from_gdrive(input_data)
            if len(df.columns) > 2:
                raise ValueError
            if ('negativeExact' not in df[1].to_list()) or ('negativePhrase' not in df[1].to_list()):
                print("Here")
                raise ValueError
            if ('negativeExact' in df[0].to_list()) or ('negativePhrase' in df[0].to_list()):
                print("Here2")
                raise ValueError
            for x in df[1].to_list():
                if (x != 'negativePhrase') and (x != 'negativeExact'):
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
                saving_module_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }
    
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
    if len(skus) == 0:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Product Ad'
        })
    else:
        for sku in skus:
            items.append({
                'Product': "Sponsored Products",
                'Entity': 'Product Ad'
            })
    for i in range(4):
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Product Targeting'
        })
    for i in range(3):
            items.append({
                'Product': "Sponsored Products",
                'Entity': "Bidding Adjustment"
            })
    for i in neg_keywords:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Negative Keyword'
        })
    df = pd.DataFrame(items, columns=cols)
    for col in cols:
        df[col] = df[col].astype('object')
    return df

def is_from_row(row, value):
    rows_values = ['SKU', 'ASIN', 'Campaign Name Modifier', 'Campaign Name Modifier', 'SKU Group Name']
    if value in rows_values:
        return row[value]
    else:
        return value
 
def make_campaign_name(row, campaign_name_order):
    campaign_name = ''
    i = 0
    while True:
        try:
            if i == 0:
                campaign_name += f"{is_from_row(row, campaign_name_order[i])}"
            else:
                campaign_name += f"_{is_from_row(row, campaign_name_order[i])}"
        except:
            break
        i += 1
    return campaign_name

def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_1):
    dfs = []
    for i, row in input_df.iterrows():
        if not pd.isna(row['Negative Targeting']):
            neg_df = hep.download_from_gdrive(row['Negative Targeting'])
            x_table = get_table(out_cols, neg_df[0].to_list())
        else:
            x_table = get_table(out_cols)
        campaign_name = make_campaign_name(row, campaign_name_order)
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


