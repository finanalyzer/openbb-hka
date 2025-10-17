import pandas as pd
from typing import List
from openbb import obb
import akshare as ak
from mysharelib.tools import normalize_symbol
from core.config import config
from . import default_provider

def get_news(ticker: str, limit: int = 10)->pd.DataFrame:
    """Get latest news for a stock"""
    return obb.news.company(ticker, provider=default_provider).to_dataframe().head(limit)

def get_info(ticker: str)->pd.DataFrame:
    """
    获取A股基本信息
    """
    from mysharelib.tools import normalize_symbol

    _, symbol_f, _ = normalize_symbol(ticker)

    df_base = obb.equity.fundamental.metrics(symbol=symbol_f, provider=default_provider).to_dataframe().T
    return df_base[0]

def get_profile(ticker: str)->pd.DataFrame:
    """
    Get company profile
    """
    from mysharelib.tools import get_timestamp
    profile_df = obb.equity.profile(symbol=ticker, provider=default_provider).to_dataframe()
    profile_df=profile_df[["symbol", "公司名称", "公司简介", "主要范围", "成立日期", "上市日期"]]
    profile_df['成立日期']=pd.to_datetime(get_timestamp(profile_df['成立日期']), unit='s').date()
    profile_df.set_index('symbol', inplace=True)
    return profile_df

def get_historical_prices(
    ticker: str,
    interval: str,
    interval_multiplier: int,
    start_date: str,
    end_date: str
    )->pd.DataFrame:
    """
    Get historical prices
    """
    return obb.equity.price.historical(symbol=ticker, start_date=start_date, end_date=end_date, provider=default_provider).to_dataframe()

def get_tickers(exchange: str = "") -> List[dict]:
    """Get available tickers for OpenBB Workspace widget."""
    result_df = obb.equity.search(provider="akshare").to_dataframe()
    if exchange == "HKEX":
        result_df = result_df[result_df['exchange'] == "HKEX"]
    else:
        result_df = result_df[result_df['exchange'] != "HKEX"]
    if not result_df.empty:
        equity_list = [
            {
                "label": row['name'] if 'name' in result_df.columns else "Unknown Company",
                "value": row['symbol'] if 'symbol' in result_df.columns else "invalid ticker",
                "extraInfo": {
                    "description": row['symbol'] if 'symbol' in result_df.columns else "invalid ticker",
                    "rightOfDescription": row['exchange'] if 'exchange' in result_df.columns else "invalid"
                }
            }
            for index, row in result_df.iterrows()
        ]
        return equity_list
    return []

def get_price(symbol: str):
    symbol_b, symbol_f, market = normalize_symbol(symbol)
    if market == "HK":
        symbol_xq = symbol_b
    else:
        symbol_xq = f"{market}{symbol_b}"
    ak.stock.cons.xq_a_token=config.akshare_api_key
    stock_individual_spot_xq_df = ak.stock_individual_spot_xq(symbol=symbol_xq)
    stock_individual_spot_xq_df.set_index('item', inplace=True)
    stock_individual_spot_xq_df.loc[["代码"]]=symbol_b
    return stock_individual_spot_xq_df.T

def get_quote(symbols: str):
    all_data = []
    list = symbols.split(",")
    for symbol in list:
        try:
            data = get_price(symbol)
            all_data.append(data[["代码", "名称", "现价", "52周最低", "52周最高", "成交量", "股息率(TTM)", "股息(TTM)"]].to_dict(orient="records")[0])
        except Exception as e:
            print(f"Error fetching data for symbol {symbol}: {e}")
            continue
    return all_data