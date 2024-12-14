import pandas as pd

def get_ecb_rates():
    data_rates = pd.read_csv(

    'data/ecb_rates.csv',
    index_col=0,
    header=0,
    names=[
        'Date',
        'Time_Period',
        'Deposit_Change',
        'Deposit_Level',
        'Lending_Change',
        'Lending_Level',
        'Refinancing_Change',
        'Fixed_Rate_Level',
        'Variable_Rate_Level',
        'Deposit_Level_Alt',
        'Fixed_Rate_Level_Alt',
        'Min_Bid_Rate_Level'
    ],
    
    parse_dates=True,

    ).drop(columns='Time_Period')

    return data_rates


