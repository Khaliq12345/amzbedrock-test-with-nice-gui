from pydantic import BaseModel, field_validator
import dateparser
import pandas as pd
from retrying import retry
import requests
import uuid
import os
from datetime import datetime

def make_the_table(row, single, out_cols):
    pa_df, pa_df_list = download_product_ads(row)
    x_table = single.get_table(out_cols, None, skus=pa_df_list)
    return x_table, pa_df
    
def parse_my_date(date_str):
    return dateparser.parse(str(date_str)).strftime("%Y%m%d")

def clean_check_input_file(input_df: pd.DataFrame):
    input_df.dropna(how='all')
    input_df = input_df.loc[2:]
    if 'Campaign Name Modifier' in input_df.columns:
        input_df["Campaign Name Modifier"] = input_df["Campaign Name Modifier"].fillna('')
    return input_df

class CommonObj(BaseModel):
    sku: str | int
    asin: str | int
    portfolio_id: int | float = 13535763995183
    activate_campaign_and_ad_group: str
    placement_product: int | float = 0
    placement_rest: int | float = 0
    placement_top: int | float = 0
    daily_budget: int | float = 0
    bid: int | float = 0
    bidding_strategy: str = 'Fixed bid'
    console: str
    start_date: str | datetime = 'today'
    
    @field_validator('portfolio_id', mode='after')
    def validate_portfolio_id(input_data: int | float):
        if pd.isna(input_data):
            raise ValueError('warning')
    
    @field_validator('start_date', mode='after')
    def validate_date(cls, input_data: str | datetime):
        try:
            return parse_my_date(input_data)
        except AttributeError:
            raise ValueError
    
    @field_validator('asin', mode='after')
    def validate_sku(cls, input_data: str|int):
        input_data = str(input_data)
        if len(input_data) != 10:
            raise ValueError
        return input_data
    
    @field_validator('activate_campaign_and_ad_group', mode='after')
    def validate_activate_campaign_and_ad_group(cls, input_data: str):
        if input_data not in ['yes', 'no']:
            raise ValueError
        return input_data
    
    @field_validator('placement_product', 'placement_rest', 'placement_top', mode='after')
    def validate_placements(cls, input_data: int | float):
        if (input_data > 900) or (input_data < 0) or (pd.isnull(input_data)):
            raise ValueError
        return input_data
    
    @field_validator("daily_budget", mode='after')
    def validate_budget(cls, input_data: int | float):
        if (pd.isnull(input_data)):
            raise ValueError
        if (input_data > 100 ):
            raise ValueError('Warning')
        return input_data

    @field_validator("bid", mode='after')
    def validate_bid(cls, input_data: int | float):
        if (pd.isnull(input_data)):
            raise ValueError
        if (input_data > 3):
            raise ValueError('Warning')
        return input_data
    
    @field_validator('bidding_strategy', mode='after')
    def validate_bidding_strategy(cls, input_data: str):
        if input_data.strip() in ['Dynamic bids - up and down', 'Dynamic bids - down only', 'Fixed bid']:
            pass
        else:
            raise ValueError
        return input_data
    
    @field_validator('console', mode='after')
    def validate_console(cls, input_data: str):
        if input_data in ["VC", "SC"]:
            pass
        else:
            raise ValueError
        return input_data

class GroupObj(BaseModel):
    sku_group_name: str
    product_ads: str
    
    @field_validator('product_ads', mode='after')
    def validate_pa_df(cls, input_data: str):
        if pd.isna(input_data):
            pass
        else:
            df = download_from_gdrive(input_data)
            if len(df.columns) != 2:
                raise ValueError
        return input_data

def saving_common_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'sku' in error['loc']:
        error_messages.append(f"Row {row.name} SKU Error: SKU is required and currently missing")
    elif 'asin' in error['loc']:
        error_messages.append(f"Row {row.name} ASIN Error: ASIN must be a 10 character string")
    elif 'portfolio_id' in error['loc']:
        if 'warning' in error['msg']:
            warning_messages.append(f"Row {row.name} Portfolio ID Warning: No portfolio ID has been added. If this is not intentional please add before continuing")
        else:
            error_messages.append(f"Row {row.name} Portfolio ID Error: Portfolio ID must be either left blank or a numeric portfolio ID")
    elif 'activate_campaign_and_ad_group' in error['loc']:
        error_messages.append(f"Row {row.name} Activate Campaign and Ad Group Error: Must be either yes or no")
    elif 'placement_product' in error['loc']:
        error_messages.append(f"Row {row.name} Placement Product Page Error: A placment percentage between 0 - 900 must be entered")
    elif 'placement_rest' in error['loc']:
        error_messages.append(f"Row {row.name} Placement Rest Of Search Error: A placment percentage between 0 - 900 must be entered")
    elif 'placement_top' in error['loc']:
        error_messages.append(f"Row {row.name} Placement Top Error: A placment percentage between 0 - 900 must be entered")
    elif 'daily_budget' in error['loc']:
        if "Warning" in error['msg']:
            warning_messages.append(f"Row {row.name} Daily Budget Warning: A daily budget above $100 is considered high for a newly created campaign. If this is not intentional please adjust before continuing")
        else:
            error_messages.append(f"Row {row.name} Daily Budget Error: A daily campaign budget must be entered")
    elif 'bid' in error['loc']:
        if 'Warning' in error['msg']:
            warning_messages.append(f"Row {row.name} Bid Warning: A bid above $3 is considered high for a newly created campaign. If this is not intentional please adjust before continuing")
        else:
            error_messages.append(f"Row {row.name} Bid Error: A bid must be entered")
    elif 'bidding_strategy' in error['loc']:
        error_messages.append(f"Row {row.name} Bidding Strategy Error: Must be one of the following: Dynamic bids - up and down, Dynamic bids - down only, Fixed bid")
    elif 'console' in error['loc']:
        error_messages.append(f"Row {row.name} Console Error: Must be either SC or VC")
    elif 'start_date' in error['loc']:
        error_messages.append(f"Row {row.name} Start Date Error: Please enter either 'today' or an exact date")

def saving_group_errors(error: dict, row, error_messages: list, warning_messages: list):
    if 'sku_group_name' in error['loc']:
        error_messages.append(f"Row {row.name} SKU Group Name Error: Please put in the Sku group name")
    elif 'product_ads' in error['loc']:
        error_messages.append(f"Row {row.name} Product Ads Error: Please ensure the link added is a Google Drive link (anyone with the link can edit) to a csv with the SKU in column A and ASIN in column B with no header row")

def add_ps_feature(func):
    def wrapper(cols: list, any_data: list, skus: list = []):
        items = func(cols, any_data, skus)
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
        df = pd.DataFrame(items, columns=cols)
        for col in cols:
            df[col] = df[col].astype('object')
        return df
    return wrapper

def download_product_ads(row):
    pa_df = None
    if not pd.isna(row['Product Ads']):
        pa_df = download_from_gdrive(row['Product Ads'])
        pa_df_list = pa_df[0].to_list()
    else:
        pa_df_list = []
    return pa_df, pa_df_list

@retry(stop_max_attempt_number=5, wait_fixed=500)
def download_from_gdrive(g_url: str):
    x_name = str(uuid.uuid1())
    output = f"./{x_name}.csv"
    g_id = g_url.removeprefix('https://drive.google.com/file/d/').split('/view?')[0]
    url = f'https://drive.google.com/uc?export=download&id={g_id}'
    response =  requests.get(url)
    with open(output,'wb') as f:
        f.write(response.content)
    df = pd.read_csv(output, header=None)
    os.remove(output)
    df.dropna(how='all', inplace=True)
    return df