import pandas as pd
import helpers as hep
from pydantic import field_validator, ValidationError, ValidationInfo
import ultraimport
cno_module_3 = ultraimport('__dir__/../campaign_names.py', 'single_cno_module_3')
out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_4_3_2_1')

def saving_module_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'expanded' in error['loc']:
        error_messages.append(f"Row {row.name} Expanded Error: Must be either y or n")
    elif 'targeting' in error['loc']:
        error_messages.append(f"Row {row.name} Targeting Error: Must be either SELF or COMP")
    elif 'targeting_url' in error['loc']:
        if 'SELF' in error['msg']:
            error_messages.append(f"Row {row.name} Targeting File Error: Targeting file is only required when Targeting = COMP")
        else:
            error_messages.append(f"Row {row.name} Targeting File Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the ASINs in column A with no header row")

class Module3(hep.CommonObj):
    expanded: str
    targeting: str
    targeting_url: str | float
    
    @field_validator('expanded', mode='after')
    def validate_expanded(cls, input_data: str):
        if input_data in ["y", "n"]:
            pass
        else:
            raise ValueError
        return input_data
    
    @field_validator('targeting', mode='after')
    def validate_targeting(cls, input_data: str):
        if input_data in ["SELF", "COMP"]:
            pass
        else:
            raise ValueError
        return input_data
    
    @field_validator('targeting_url', mode='after')
    def validate_targeting_url(cls, input_data: str | float, info: ValidationInfo):
        try:
            t = info.data['targeting']
            if (pd.isna(input_data)) and (t == 'COMP'):
                raise ValueError
            elif (pd.isna(input_data)) and (t == 'SELF'):
                pass
            elif (t == 'SELF') and (not pd.isna(input_data)):
                raise ValueError('SELF')
            else:
                df = hep.download_from_gdrive(input_data)
                if len(df.columns) != 1:
                    raise ValueError
        except KeyError:
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
                'expanded': row['Expanded?'],
                'targeting': row['Targeting'],
                'targeting_url': row['Targeting File'],
            }
            row_obj = Module3(**row_json)
        except ValidationError as e:
            for error in e.errors():
                hep.saving_common_errors(error, row, error_messages, warning_messages)
                saving_module_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }

@hep.add_ps_feature
def get_table(cols: list, asins:list, skus: list = []):
    items = []
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Campaign'
    })
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Ad Group'
    })
    for asin in asins:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Product Targeting'
        })
    for i in range(3):
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Bidding Adjustment"
        })
    return items

def is_from_row(row, value):
    row_values = ['SKU', 'ASIN', 'Targeting', 'Campaign Name Modifier', 'SKU Group Name']
    if value in row_values:
        return row[value]
    elif value == 'Expanded':
        if row['Expanded?'] == 'y':
            return 'Expanded'
        else:
            return ''
    else:
        return value

def make_campaign_name(row, campaign_name_order: dict):
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
    
def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_3):
    dfs = []
    for i, row in input_df.iterrows():
        #Entity and Sponsored Product
        if row['Targeting'] == 'SELF':
            x_table = get_table(out_cols, [row['ASIN']])
        else:
            asins = hep.download_from_gdrive(row['Targeting File'])[0].to_list()
            x_table = get_table(out_cols, asins)
        #create
        x_table.loc[:, 'Operation'] = 'create'
        #campaign name
        campaign_name = make_campaign_name(row, campaign_name_order)
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
        #start date
        x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = hep.parse_my_date(row['Start Date'])
        #targeting type
        x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
        #state
        enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
        x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
        x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
        x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = 'enabled'
        #daily budget
        x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
        #sku and asin
        console_sc_vc = lambda x, y, value: y if x == value else None
        x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
        x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
        #Ad group default bid
        x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
        #Bidding adj
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
        #Product Targeting
        if row['Targeting'] == 'SELF':
            if row['Expanded?'] == 'y':
                targets = f'asin-expanded="{row["ASIN"]}"'
            else:
                targets = f'asin="{row["ASIN"]}"'
        else:
            if row['Expanded?'] == 'y':
                targets = [f'asin-expanded="{t}"' for t in asins]
            else:
                targets = [f'asin="{t}"' for t in asins]
        x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = targets
        dfs.append(x_table)
    
    output_dataframe = pd.concat(dfs, ignore_index=True)
    output_dataframe['Keyword Text'] = output_dataframe['Keyword Text'].replace('nan', pd.NA)
    output_dataframe['Match Type'] = output_dataframe['Match Type'].replace('nan', pd.NA)
    return output_dataframe



