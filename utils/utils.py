import time
import pandas as pd


def get_previous_values(date, n, df2):
    """Get the content of df2 from the n days before date
    """
    start_date = date - pd.Timedelta(days=n)
    result = df2[(df2.index >= start_date) & (df2.index <= date)]['content'].tolist()

    return result
