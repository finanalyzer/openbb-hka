from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from typing import List
import json
import asyncio
import numpy as np
from openbb import obb
from core.registry import register_widget

tradingview_router = APIRouter()

@tradingview_router.get("/config")
async def get_config():
    """UDF configuration endpoint"""
    return {
        "supported_resolutions": ["1", "5", "15", "30", "60", "D", "W", "M"],
        "supports_group_request": False,
        "supports_marks": False,
        "supports_search": True,
        "supports_timescale_marks": False,
        "supports_time": True,
        "exchanges": [
            {"value": "", "name": "All Exchanges", "desc": ""},
            {"value": "SSE", "name": "SSE", "desc": "Shanghai Stock Exchange"},
            {"value": "SZSE", "name": "SZSE", "desc": "Shenzhen Stock Exchange"},
            {"value": "BSE", "name": "BSE", "desc": "Beijing Stock Exchange"},
            {"value": "HKEX", "name": "HKEX", "desc": "Hong Kong Stock Exchange"}
        ],
        "symbols_types": [
            {"name": "All types", "value": ""},
            {"name": "Stocks", "value": "stock"}
        ]
    }

@tradingview_router.get("/search")
async def search_symbols(
    query: str = Query("", description="Search query"),
    limit: int = Query(30, description="Limit of results")
):
    """Search symbols for TradingView UDF frontend.

    Returns a list of objects with fields matching TradingView's
    search response: symbol, full_name, description, exchange, type.
    """
    try:
        df = obb.equity.search(provider="akshare").to_dataframe()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying symbols provider: {e}")

    if df is None or df.empty:
        return []

    q = query.strip()
    results = []

    # If query empty, return top N
    if q == "":
        candidates = df.head(limit)
    else:
        # Prioritize symbol exact match, then symbol startswith, then name contains
        candidates = pd.DataFrame()
        if 'symbol' in df.columns:
            exact = df[df['symbol'].str.lower() == q.lower()]
            starts = df[df['symbol'].str.lower().str.startswith(q.lower())]
            candidates = pd.concat([exact, starts])
        if 'name' in df.columns:
            name_contains = df[df['name'].str.contains(q, case=False, na=False)]
            candidates = pd.concat([candidates, name_contains])
        # drop duplicates while preserving order
        if not candidates.empty:
            candidates = candidates.drop_duplicates(subset=['symbol'], keep='first')
        else:
            candidates = df

        candidates = candidates.head(limit)

    for _, row in candidates.iterrows():
        symbol = row.get('symbol') if 'symbol' in row.index else None
        name = row.get('name') if 'name' in row.index else None
        exchange = row.get('exchange') if 'exchange' in row.index else None

        results.append({
            'symbol': symbol or "",
            'full_name': f"{exchange}:{symbol}" if exchange and symbol else (symbol or ""),
            'description': name or "",
            'exchange': exchange or "",
            'type': 'stock'
        })

    return results

@tradingview_router.get("/symbols")
async def get_symbol_info(symbol: str = Query(..., description="Symbol to get info for")):
    """Return TradingView UDF symbol info for a given symbol.

    Uses OpenBB (akshare provider) to search for the symbol and maps
    the result to the TradingView UDF symbol info schema.
    """
    try:
        result_df = obb.equity.search(provider="akshare").to_dataframe()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying symbols provider: {e}")

    if result_df is None or result_df.empty:
        raise HTTPException(status_code=404, detail="No symbols available from provider")

    # Accept symbols like "EXCHANGE:SYMBOL" or plain "SYMBOL"
    search_symbol = symbol
    exchange_part = None
    if ":" in symbol:
        exchange_part, search_symbol = symbol.split(":", 1)

    match = None
    if 'symbol' in result_df.columns:
        df_match = result_df[result_df['symbol'] == search_symbol]
        if df_match.empty and exchange_part is not None:
            df_match = result_df[(result_df['symbol'] == search_symbol) & (result_df.get('exchange') == exchange_part)]
        if df_match.empty:
            df_match = result_df[result_df['symbol'] == symbol]
        if not df_match.empty:
            match = df_match.iloc[0]

    if match is None and 'name' in result_df.columns:
        df_match = result_df[result_df['name'].str.contains(search_symbol, na=False)]
        if not df_match.empty:
            match = df_match.iloc[0]

    if match is None:
        raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol}")

    exchange = match.get('exchange') if 'exchange' in match.index else None
    name = match.get('name') if 'name' in match.index else match.get('symbol')
    ticker = match.get('symbol') if 'symbol' in match.index else symbol

    timezone = "UTC"
    session = "0900-1700"
    if exchange in ("SSE", "SZSE", "BSE"):
        timezone = "Asia/Shanghai"
        session = "0930-1130,1300-1500"
    elif exchange == "HKEX":
        timezone = "Asia/Hong_Kong"
        session = "0930-1200,1300-1600"

    pricescale = 100
    if 'precision' in match.index:
        try:
            prec = int(match.get('precision', 2))
            pricescale = 10 ** prec
        except Exception:
            pricescale = 100

    response = {
        "name": name,
        "ticker": ticker,
        "description": name or "",
        "type": "stock",
        "session": session,
        "exchange": exchange or "",
        "listed_exchange": exchange or "",
        "timezone": timezone,
        "minmov": 1,
        "pricescale": pricescale,
        "has_intraday": True,
        "has_no_volume": False,
        "has_daily": True,
        "has_weekly": True,
        "has_monthly": True,
        "supported_resolutions": ["1", "5", "15", "30", "60", "D", "W", "M"]
    }

    return response

@register_widget({
        "name": "TradingView Charting",
        "description": "Advanced charting for China and Hong Kong stocks using TradingView UDF protocol.",
        "category": "Finance",
        "type": "advanced_charting",
        "endpoint": "/udf",
        "gridData": {
            "w": 20,
            "h": 20
        },
        "data": {
            "defaultSymbol": "600325",
            "updateFrequency": 60000
        }
})
@tradingview_router.get("/history")
async def get_history(
    symbol: str = Query(..., description="Symbol"),
    resolution: str = Query(..., description="Resolution"),
    from_time: int = Query(..., alias="from", description="From timestamp"),
    to_time: int = Query(..., alias="to", description="To timestamp")
):
    """TradingView UDF history endpoint.

    Returns OHLCV data between `from_time` and `to_time` inclusive.
    Supports daily/weekly/monthly resolutions and numeric minute resolutions
    when intraday data is available from the provider.
    """
    # parse timestamps
    try:
        start_dt = pd.to_datetime(from_time, unit='s')
        end_dt = pd.to_datetime(to_time, unit='s')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid from/to timestamps: {e}")

    # fetch data
    try:
        df = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_dt.date().isoformat(),
            end_date=end_dt.date().isoformat(),
            provider="akshare"
        ).to_dataframe()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical prices: {e}")

    if df is None or df.empty:
        return {"s": "no_data"}

    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            pass

    # filter to requested window
    df = df[(df.index >= start_dt) & (df.index <= end_dt)]
    if df.empty:
        return {"s": "no_data"}

    # helper to map lower-case column name to actual
    cols = {c.lower(): c for c in df.columns}
    def col(name):
        return cols.get(name, name)

    res = resolution.upper()
    resampled = None
    try:
        if res in ("D", "1D"):
            resampled = df
        elif res in ("W", "1W"):
            resampled = df.resample('W').agg({col('open'): 'first', col('high'): 'max', col('low'): 'min', col('close'): 'last', col('volume'): 'sum'})
        elif res in ("M", "1M"):
            resampled = df.resample('M').agg({col('open'): 'first', col('high'): 'max', col('low'): 'min', col('close'): 'last', col('volume'): 'sum'})
        else:
            # numeric minute resolution
            try:
                minutes = int(resolution)
                diffs = df.index.to_series().diff().dropna()
                if not diffs.empty and diffs.min() < pd.Timedelta('1D'):
                    rule = f"{minutes}T"
                    resampled = df.resample(rule).agg({col('open'): 'first', col('high'): 'max', col('low'): 'min', col('close'): 'last', col('volume'): 'sum'})
                else:
                    return {"s": "no_data"}
            except ValueError:
                return {"s": "no_data"}
    except Exception:
        return {"s": "no_data"}

    if resampled is None or resampled.empty:
        return {"s": "no_data"}

    close_col = col('close')
    if close_col in resampled.columns:
        resampled = resampled.dropna(subset=[close_col])
    if resampled.empty:
        return {"s": "no_data"}

    try:
        t = (resampled.index.astype('int64') // 10**9).astype(int).tolist()
    except Exception:
        t = [int(dt.timestamp()) for dt in resampled.index.to_pydatetime()]

    def series_list(n):
        if n in resampled.columns:
            return [None if pd.isna(x) else float(x) for x in resampled[n].tolist()]
        return [None] * len(resampled)

    o = series_list(col('open'))
    h = series_list(col('high'))
    l = series_list(col('low'))
    c = series_list(col('close'))
    v = series_list(col('volume'))

    return {"s": "ok", "t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


@tradingview_router.get("/time")
async def get_server_time():
    """Return current server time as Unix timestamp (seconds since epoch)."""
    import time
    return int(time.time())