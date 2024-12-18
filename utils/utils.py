import time
import pandas as pd


def get_previous_values(date, n, df2, col="content"):
    """Get the content of df2 from the n days before date
    """
    start_date = date - pd.Timedelta(days=n)
    result = df2[(df2.index >= start_date) & (df2.index <= date)][col].tolist()

    return result


def get_delta(df, column):
    df[f'delta_{column}'] = df[column] - df[column].shift(1)
    df[f"dummy_{column}"] = df[f'delta_{column}'].apply(lambda x: 1 if x > 0 else (0 if x == 0 else -1))
    return df
