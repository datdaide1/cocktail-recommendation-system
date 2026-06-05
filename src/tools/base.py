import pandas as pd
from src.utils.config import Config

def get_cocktails_df():
    try:
        return pd.read_csv(Config.COCKTAILS_PATH).fillna("")
    except Exception as e:
        print(f"Error loading cocktails: {e}")
        return pd.DataFrame()

def get_bars_df():
    try:
        return pd.read_csv(Config.BARS_PATH).fillna("")
    except Exception as e:
        print(f"Error loading bars: {e}")
        return pd.DataFrame()
