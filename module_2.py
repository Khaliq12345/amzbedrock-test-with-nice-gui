import pandas as pd
from pydantic import field_validator, ValidationError, model_validator, ValidationInfo
from retrying import retry
import helpers as hep

out_cols = ['Product',
 'Entity',
 'Operation',
 'Campaign ID',
 'Ad Group ID',
 'Portfolio ID',
 'Ad ID',
 'Keyword ID',
 'Product Targeting ID',
 'Campaign Name',
 'Ad Group Name',
 'Start Date',
 'End Date',
 'Targeting Type',
 'State',
 'Daily Budget',
 'SKU',
 'ASIN',
 'Ad Group Default Bid',
 'Bid',
 'Keyword Text',
 'Match Type',
 'Bidding Strategy',
 'Placement',
 'Percentage',
 'Product Targeting Expression']

CAMPAIGN_NAME_ORDER = {
    0: 'SKU',
    1: 'SP',
    2: 'KW',
    3: 'Match Type',
    4: 'ASIN',
    5: 'Campaign Name Modifier',
    6: 'Keyword'
}

def saving_module_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'single_group_kw' in error['loc']:
        error_messages.append(f"Row {row.name} Single/Group KWs Error: Must be either Single or Group")
    elif 'match_type' in error['loc']:
        error_messages.append(f"Row {row.name} Match Type Error: Must be one of the following: Exact, Phrase, Broad")
    elif 'branded_campaign' in error['loc']:
        error_messages.append(f"Row {row.name} Branded Campaign Error: Must be either y or n")
    elif 'brand_name' in error['loc']:
        error_messages.append(f"Row {row.name} Brand Name Error: brand name must be added for a branded campaign")
    elif 'keyword_link' in error['loc']:
        error_messages.append(f"Row {row.name} Keyword Link Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the keywords in column A with no header row")
    elif 'negative_url' in error['loc']:
        error_messages.append(f"Row {row.name} Negative Targeting Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the keyword in column A and match type in column B with no header row")

class Module2(hep.CommonObj):
    single_group_kw: str
    match_type: str
    branded_campaign: str | float
    brand_name: str | float
    keyword_link: str
    negative_url: str | float
    
    @field_validator('branded_campaign', mode='after')
    def validate_yes_no(cls, input_data: str | float):
        if pd.isna(input_data):
            pass
        else:
            if input_data in ["y", "n"]:
                pass
            else:
                raise ValueError
        return input_data
    
    @field_validator('single_group_kw', mode='after')
    def validate_single_group_kw(cls, input_data: str):
        if input_data in ["Single", "Group"]:
            pass
        else:
            raise ValueError
    
    @field_validator('match_type', mode='after')
    def validate_match_type(cls, input_data: str):
        if input_data in ["Exact", "Phrase", "Broad"]:
            pass
        else:
            raise ValueError
        return input_data

    @field_validator('brand_name', mode='after')
    def validate_brand_name(cls, input_data: str | float, info: ValidationInfo):
        try:
            bc = info.data['branded_campaign'] == 'y'
            if (bc) and (pd.isna(input_data)):
                raise ValueError
        except KeyError:
            raise ValueError
        return input_data
    
    @field_validator('keyword_link', mode='after')
    def valudate_keyword_link(cls, input_data: str):
        df = hep.download_from_gdrive(input_data)
        if len(df.columns) != 1:
            raise ValueError
    
    @field_validator('negative_url', mode='after')
    def validate_df(cls, input_data: str | float):
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
                'single_group_kw': row['Single/Group KWs'],
                'match_type': row['Match Type'],
                'branded_campaign': row['Branded Campaign?'],
                'brand_name': row['brand name'],
                'keyword_link': row['Keyword Link'],
                'negative_url': row['Negative Targeting'],
            }
            row_obj = Module2(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                saving_module_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }

def get_table(cols: list, keyword_type: str, keywords: list, neg_keywords: list = []):
    items = []
    if keyword_type == 'Single':
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
            'Entity': 'Product Ad'
        })
        for i in range(3):
                items.append({
                    'Product': "Sponsored Products",
                    'Entity': "Bidding Adjustment"
                })
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Keyword', 
        })
    else:
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
            'Entity': 'Product Ad'
        })
        for i in range(3):
                items.append({
                    'Product': "Sponsored Products",
                    'Entity': "Bidding Adjustment"
                })
        for keyword in keywords:
            items.append({
                'Product': "Sponsored Products",
                'Entity': 'Keyword', 
            })
    
    for _ in neg_keywords:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Negative Keyword', 
        })
    df = pd.DataFrame(items, columns=cols)
    for col in cols:
        df[col] = df[col].astype('object')
    return df

def is_from_row(row, value, kws):
    no_nan = lambda x: '' if type(x) != str else x
    branded_or_name = lambda x: 'Branded' if row['Branded Campaign?'] == 'y' else f'{x}'
    campaign_name_mod = no_nan(row['Campaign Name Modifier'])
    rows_values = ['SKU', 'ASIN', 'Match Type']
    if value in rows_values:
        return row[value]
    elif value == 'Campaign Name Modifier':
        return branded_or_name(campaign_name_mod)
    elif value == 'Keyword':
        if row['Single/Group KWs'] == 'Single':
            return kws
        else:
            return ''
    else:
        return value

def modify_table(row, x_table, kw_type, kws, neg_info: list = [], campaign_name_order: dict = CAMPAIGN_NAME_ORDER):
    #Generating the campaign name
    a = is_from_row(row, campaign_name_order[0], kws)
    b = is_from_row(row, campaign_name_order[1], kws)
    c = is_from_row(row, campaign_name_order[2], kws)
    d = is_from_row(row, campaign_name_order[3], kws)
    e = is_from_row(row, campaign_name_order[4], kws)
    f = is_from_row(row, campaign_name_order[5], kws)
    g = is_from_row(row, campaign_name_order[6], kws)
    
    single_kw = f"{a}_{b}_{c}_{d}_{e}_{f}_{g}"
    kw_not_single = f"{a}_{b}_{c}_{d}_{e}_{f}_{g}"
    #make_campaign_name = lambda x: single_kw if 'Single' in x else kw_not_single #make campaign name
    #campaign_name = make_campaign_name(row['Single/Group KWs'])
    campaign_name = f"{a}_{b}_{c}_{d}_{e}_{f}_{g}"
    
    #operation
    x_table.loc[:, 'Operation'] = 'create'
    
    #campaign id
    x_table.loc[:, 'Campaign ID'] = campaign_name
    
    #ad group id
    x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
    
    #portfolio id
    x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
    
    #campaign name
    x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
    
    #ad group name
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
    
    #date
    x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = hep.parse_my_date(row['Start Date'])
    
    #targeting type
    x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
    
    #state
    enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
    x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
    x_table.loc[~(x_table['Entity'].isin(['Campaign', 'Ad Group', 'Product Ad', 'Bidding Adjustment'])), 'State'] = 'enabled'
    x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])

    #daily budget
    x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
    
    #sku and asin
    console_sc_vc = lambda x, y, value: y if x == value else ''
    x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
    x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
    
    #bid
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
    
    #keyword text
    if 'Single' in kw_type:
        target_kw = kws
        if row['Branded Campaign?'] == 'y':
            target_kw = f"{row['brand name']} {kws}"
    else:
        target_kw = kws
        if row['Branded Campaign?'] == 'y':
            target_kw = [f"{row['brand name']} {x}" for x in  target_kw] 
    x_table.loc[x_table['Entity'] == 'Keyword', 'Keyword Text'] = target_kw
    
    #match type
    x_table.loc[x_table['Entity'] == 'Keyword', 'Match Type'] = row['Match Type']
    
    #bidding strategy
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
    #adding negative keyword data
    if not pd.isna(row['Negative Targeting']):
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Campaign ID'] = campaign_name
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'State'] = 'enabled'
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Keyword Text'] = neg_info[0]
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Match Type'] = neg_info[1]
    return x_table
    
def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = CAMPAIGN_NAME_ORDER):
    dfs = []
    for i, row in input_df.iterrows():
        #get the row table
        if 'Single' in row['Single/Group KWs']:
            kws = hep.download_from_gdrive(row['Keyword Link'])[0].to_list()
            for kw in kws:
                if not pd.isna(row['Negative Targeting']):
                    neg_df = hep.download_from_gdrive(row['Negative Targeting'])
                    x_table = get_table(out_cols, row['Single/Group KWs'], kw, neg_keywords=neg_df[0].to_list())
                    x_table = modify_table(row, x_table, 'Single', kw, 
                                            neg_info=[neg_df[0].to_list(), 
                                                        neg_df[1].to_list()],
                                            campaign_name_order=campaign_name_order)
                else:
                    x_table = get_table(out_cols, row['Single/Group KWs'], kw)
                    x_table = modify_table(row, x_table, 
                                            'Single', 
                                            kw,
                                            campaign_name_order=campaign_name_order)
                dfs.append(x_table)
        else:
            kws = hep.download_from_gdrive(row['Keyword Link'])[0].to_list()
            if not pd.isna(row['Negative Targeting']):
                neg_df = hep.download_from_gdrive(row['Negative Targeting'])
                x_table = get_table(out_cols, row['Single/Group KWs'], kws, neg_keywords=neg_df[0].to_list())
                x_table = modify_table(row, x_table, 
                                        'Group', 
                                        kws, 
                                        neg_info=[neg_df[0].to_list(), 
                                                    neg_df[1].to_list()],
                                        campaign_name_order=campaign_name_order)
            else:
                x_table = get_table(out_cols, row['Single/Group KWs'], kws)
                x_table = modify_table(row, x_table, 
                                        'Group', 
                                        kws,
                                        campaign_name_order=campaign_name_order)      
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    output_dataframe['Keyword Text'] = output_dataframe['Keyword Text'].replace('nan', pd.NA)
    output_dataframe['Match Type'] = output_dataframe['Match Type'].replace('nan', pd.NA)
    return output_dataframe

