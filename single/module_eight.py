import pandas as pd
import helpers as hep
from pydantic import field_validator, ValidationInfo, ValidationError, BaseModel #remove repetition codes #check the bid of other modules #validate other modules
import ultraimport
cno_module_8 = ultraimport('__dir__/../campaign_names.py', 'single_cno_module_7_8')

out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_5_6_7_8')

def saving_module_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'bid_mod' in error['loc']:
        if 'warning 3' in error['msg']:
            warning_messages.append(f"Row {row.name} Bid Warning: A cpc bid above $3 is considered high. If this is not intentional please adjust before continuing")
        elif 'warning 10' in error['msg']:
            warning_messages.append(f"Row {row.name} Bid Warning: A vcpm bid below $10 is considered low. If this is not intentional please adjust before continuing")
        else:
            error_messages.append(f"Row {row.name} Bid Error: A bid must be entered")
    elif 'audience_targeting' in error['loc']:
        error_messages.append(f"Row {row.name} Audience Targeting Error: Must be exactly one of views-Category, purchases-Category")
    elif 'bid_optimization' in error['loc']:
        error_messages.append(f"Row {row.name} Bid Optimization Error: Must be one of Optimize for page visits, Optimize for conversions, Optimize for viewable impressions")
    elif 'lookback' in error['loc']:
        error_messages.append(f"Row {row.name} Lookback Error: Must be exactly one of 7 days, 14 days, 30 days, 60 days, 90 days")
    elif 'audience_targeting_file' in error['loc']:
        error_messages.append(f"Row {row.name} Audience Targeting File Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the category code in column A and category name in column B with no header row")
    
class Module8(hep.CommonObj):
    bid_optimization: str
    bid_mod: int
    audience_targeting: str
    lookback: str
    audience_targeting_file: str
    
    @field_validator('bid_mod', mode='after')
    def validate_bid_mod(cls, input_data: int, info: ValidationInfo):
        try:
            bid_optim = info.data['bid_optimization']
            if bid_optim in ['Optimize for page visits', 'Optimize for conversions']:
                if input_data > 3:
                    raise ValueError('warning 3')
            elif bid_optim == 'Optimize for viewable impressions':
                if input_data < 10:
                    raise ValueError('warning 10')
        except KeyError as e:
            raise ValueError
        return input_data
    
    @field_validator('audience_targeting', mode='after')
    def validate_audience_targeting(cls, input_data: str | float):
        audience_targetings = ['views-Category', 'purchases-Category']
        if pd.isna(input_data):
            raise ValueError
        elif input_data not in audience_targetings:
            raise ValueError
        return input_data
    
    @field_validator('lookback', mode='after')
    def validate_lookback(cls, input_data: str | float):
        lookbacks = ['7 days', '14 days', '30 days', '60 days', '90 days']
        if pd.isna(input_data):
            raise ValueError
        elif input_data not in lookbacks:
            raise ValueError
        return input_data
    
    @field_validator('bid_optimization', mode='after')
    def validate_bid_optimization(cls, input_data: str):
        optims = ['Optimize for page visits', 'Optimize for conversions', 'Optimize for viewable impressions']
        if input_data not in optims:
            raise ValueError
        return input_data

    @field_validator('audience_targeting_file', mode='after')
    def validate_audience_targeting_file(cls, input_data: str):
        if pd.isna(input_data):
            raise ValueError
        else:
            df = hep.download_from_gdrive(input_data)
            if len(df.columns) != 2:
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
                'daily_budget': row['Daily Budget'],
                'bid_mod': row["Bid"],
                'console': row['Console'],
                'start_date': row['Start Date'],
                'bid_optimization': row['Bid Optimization'],
                'audience_targeting': row['Audience Targeting'],
                'lookback': row['Lookback'],
                'audience_targeting_file': row['Audience Targeting Targeting File']
            }
            row_obj = Module8(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                saving_module_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }

@hep.add_ps_feature
def get_table(out_cols, any_data, skus: list = []):
    items = []
    items.append({
        'Product': "Sponsored Display",
        'Entity': 'Campaign'
    })
    items.append({
        'Product': "Sponsored Display",
        'Entity': 'Ad Group'
    })
    items.append({
        'Product': "Sponsored Display",
        'Entity': "Audience Targeting"
    })
    return items

def is_from_row(row, value, tev, cost_type):
    row_values = ['ASIN', 'SKU', 'Campaign Name Modifier', 'SKU Group Name']
    if value in row_values:
        return row[value]
    elif value == 'cost_type':
        return cost_type
    elif value  == 'Targeting Value':
        return tev
    else:
        return value

def make_campaign_name(row, campaign_name_order, tev, cost_type):
    campaign_name = ''
    i = 0
    while True:
        try:
            if i == 0:
                campaign_name += f"{is_from_row(row, campaign_name_order[i], tev, cost_type)}"
            else:
                campaign_name += f"_{is_from_row(row, campaign_name_order[i], tev, cost_type)}"
        except:
            break
        i += 1
    return campaign_name

def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_8):
    dfs = []
    for i, row in input_df.iterrows():
        tc_df = hep.download_from_gdrive(row['Audience Targeting Targeting File'])
        targetings, categories = tc_df[0].to_list(), tc_df[1].to_list()
        for cat, cat_name in zip(targetings, categories):
            x_table = get_table(out_cols, None)
            x_table.loc[:, 'Operation'] = 'create'
            #cost type
            cost_type_campaign = lambda x: f"cpc_{x.split(' ')[-1]}" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else f"vcpm_{x.split(' ')[-1]}"
            cost_type_selector =  lambda x: "cpc" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else "vcpm"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
            #targeting expression
            if 'views-Category' in row['Audience Targeting']:
                targeting_exp_value = f'views=(category="{cat}" lookback={row["Lookback"].replace(" days", "").strip()})'
                tev = f"views-category-{cat_name}-lookback-{row['Lookback']}"
            elif 'purchases-Category' in row['Audience Targeting']:
                targeting_exp_value = f'purchases=(category="{cat}" lookback={row["Lookback"].replace(" days", "").strip()})'
                tev = f"purchases-category-{cat_name}-lookback-{row['Lookback']}"
            else:
                targeting_exp_value = None
            x_table.loc[x_table['Entity'] == 'Audience Targeting', 'Targeting Expression'] = targeting_exp_value
            #campaign name
            cost_type = cost_type_campaign(row['Bid Optimization'])
            campaign_name = make_campaign_name(row, campaign_name_order, tev, cost_type)
            
            x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00030'
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
            x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
            x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
            #Bid
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
            #Bid optimization
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Bid Optimization'] = row['Bid Optimization']
            dfs.append(x_table)
    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe