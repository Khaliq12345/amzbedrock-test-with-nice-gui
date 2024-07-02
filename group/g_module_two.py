import pandas as pd
import helpers as hep
from pydantic import field_validator, ValidationError
from nicegui import ui
import ultraimport
cno_module_2 = ultraimport('__dir__/../campaign_names.py', 'group_cno_module_2')
out_cols = ultraimport('__dir__/../campaign_names.py', 'single_out_col_4_3_2_1')
single = ultraimport('__dir__/../single/module_two.py')
        
class Module2(hep.GroupObj, single.Module2):
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
                single.saving_module_errors(error, row, error_messages, warning_messages)
                hep.saving_group_errors(error, row, error_messages, warning_messages)

    return {
        'error_messages': list(set(error_messages)),
        'warning_messages': list(set(warning_messages))
    }
    
def proccess_df(input_df: pd.DataFrame, campaign_name_order: dict = cno_module_2):
    dfs = []
    for i, row in input_df.iterrows():
        pa_df, pa_df_list = hep.download_product_ads(row)
        #get the row table
        if 'Single' in row['Single/Group KWs']:
            kws = hep.download_from_gdrive(row['Keyword Link'])[0].to_list()
            for kw in kws:
                if not pd.isna(row['Negative Targeting']):
                    neg_df = hep.download_from_gdrive(row['Negative Targeting'])
                    x_table = single.get_table(out_cols, row['Single/Group KWs'], kw, neg_keywords=neg_df[0].to_list(), skus=pa_df_list)
                    x_table = single.modify_table(row, x_table, 'Single', kw, 
                                            neg_info=[neg_df[0].to_list(), 
                                                        neg_df[1].to_list()],
                                            campaign_name_order=campaign_name_order, pa_df=pa_df)
                else:
                    x_table = single.get_table(out_cols, row['Single/Group KWs'], kw, skus=pa_df_list)
                    x_table = single.modify_table(row, x_table, 
                                            'Single', 
                                            kw,
                                            campaign_name_order=campaign_name_order, pa_df=pa_df)
                dfs.append(x_table)
        else:
            kws = hep.download_from_gdrive(row['Keyword Link'])[0].to_list()
            if not pd.isna(row['Negative Targeting']):
                neg_df = hep.download_from_gdrive(row['Negative Targeting'])
                x_table = single.get_table(out_cols, row['Single/Group KWs'], kws, neg_keywords=neg_df[0].to_list(), skus=pa_df_list)
                x_table = single.modify_table(row, x_table, 
                                        'Group', 
                                        kws, 
                                        neg_info=[neg_df[0].to_list(), 
                                                    neg_df[1].to_list()],
                                        campaign_name_order=campaign_name_order, pa_df=pa_df)
            else:
                x_table = single.get_table(out_cols, row['Single/Group KWs'], kws, skus=pa_df_list)
                x_table = single.modify_table(row, x_table, 
                                        'Group', 
                                        kws,
                                        campaign_name_order=campaign_name_order, pa_df=pa_df)      
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    output_dataframe['Keyword Text'] = output_dataframe['Keyword Text'].replace('nan', pd.NA)
    output_dataframe['Match Type'] = output_dataframe['Match Type'].replace('nan', pd.NA)
    return output_dataframe


