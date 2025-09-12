from fastapi import APIRouter, Query, Depends
from core.registry import register_widget
import pandas as pd
from typing import List
import json
import asyncio
import numpy as np
from core.auth import get_current_user

equity_hk_router = APIRouter()

@equity_hk_router.get("/candles")
@register_widget({
    "name": "港股k线图",
    "description": "港股k线图",
    "category": "Equity",
    "type": "chart",
    "endpoint": "hk/candles",
    "widgetId": "hk/candles",
    "gridData": {
        "w": 40,
        "h": 20
    },
    "source": "AKShare",
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300.HK",
            "description": "Stock ticker (e.g., 00300.HK for Hong Kong Stock Exchange)",
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "text",
            "value": "day",
            "paramName": "interval",
            "label": "Interval",
            "description": "Time interval for prices",
            "options": [
                {"value": "minute", "label": "Minute"},
                {"value": "day", "label": "Day"},
                {"value": "week", "label": "Week"},
                {"value": "month", "label": "Month"},
                {"value": "year", "label": "Year"}
            ]
        },
        {
            "type": "number",
            "paramName": "interval_multiplier",
            "label": "Interval Multiplier",
            "value": "1",
            "description": "Multiplier for the interval (e.g., 5 for every 5 minutes)"
        },
        {
            "type": "date",
            "paramName": "start_date",
            "label": "Start Date",
            "value": "2024-09-08",
            "description": "Start date for historical data"
        },
        {
            "type": "date",
            "paramName": "end_date",
            "label": "End Date",
            "value": "2025-09-8",
            "description": "End date for historical data"
        }
    ],
    "data": {"chart": {"type": "candlestick"}},
})
async def get_candles_hk(
    ticker: str,
    interval: str,
    interval_multiplier: int,
    start_date: str,
    end_date: str
):
    from routes.charts import get_chart_data
    return get_chart_data(ticker, interval, interval_multiplier, start_date, end_date)

@equity_hk_router.get("/tickers")
def get_stock_tickers():
    """Get available stock tickers for Hong Kong market"""
    return [
        {"label": "美的集团", "value": "00300"},
        {"label": "中国人民", "value": "01339"},
        {"label": "招商局港", "value": "00144"},
        {"label": "香港电讯", "value": "06823"},
        {"label": "中国石油", "value": "00386"},
        {"label": "邮储银行", "value": "01658"},
        {"label": "辽港股份", "value": "02880"},
        {"label": "中国银行", "value": "03988"},
        {"label": "中信证券", "value": "06030"},
        {"label": "中信银行", "value": "00998"},
        {"label": "农业银行", "value": "01288"},
        {"label": "招商银行", "value": "03968"},
        {"label": "中银香港", "value": "02388"},
        {"label": "汇丰控股", "value": "00005"},
        {"label": "建设银行", "value": "00939"},
        {"label": "工商银行", "value": "01398"}
    ]

@register_widget({
    "name": "港股基本信息",
    "description": "获取港股基本信息",
    "category": "Equity",
    "subcategory": "Company Info",
    "type": "markdown",
    "widgetId": "hk/key_metrics",
    "endpoint": "hk/key_metrics",
    "gridData": {
        "w": 10,
        "h": 12
    },
    "data": {
        "table": {
            "showAll": True,
            "columns": [
                {"field": "fact", "headerName": "Fact", "width": 200},
                {"field": "value", "headerName": "Value", "width": 200}
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Ticker to get company facts for Hong Kong market",
            "optionsEndpoint": "hk/tickers"
        }
    ]
})
@equity_hk_router.get("/key_metrics")
def get_key_metrics(
    ticker: str
    ):
    """
        Get key metrics for a ticker
        "optionsEndpoint": "hk/tickers"
    """
    from fin_data.profile import get_info
    key_metrics = get_info(ticker)
    key_metrics.name = ticker
    return key_metrics.to_markdown()

@register_widget({
    "name": "港股历史股价",
    "description": "Get historical price data for stocks.",
    "category": "Equity",
    "subcategory": "Prices",
    "type": "table",
    "widgetId": "hk/prices",
    "endpoint": "hk/prices",
    "gridData": {
        "w": 40,
        "h": 8
    },
    "data": {
        "table": {
            "enableCharts": True,
            "showAll": False,
            "chartView": {
                "enabled": True,
                "chartType": "line"
            },
            "columnsDefs": [
                {"field": "date", "headerName": "Date", "width": 180, "chartDataType": "time"},
                {"field": "open", "headerName": "Open", "width": 120, "cellDataType": "number"},
                {"field": "high", "headerName": "High", "width": 120, "cellDataType": "number"},
                {"field": "low", "headerName": "Low", "width": 120, "cellDataType": "number"},
                {"field": "close", "headerName": "Close", "width": 120, "chartDataType": "series"},
                {"field": "volume", "headerName": "Volume", "width": 120, "cellDataType": "number"}
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300.HK",
            "description": "Stock ticker to get historical prices",
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "text",
            "value": "day",
            "paramName": "interval",
            "label": "Interval",
            "description": "Time interval for prices",
            "options": [
                {"value": "minute", "label": "Minute"},
                {"value": "day", "label": "Day"},
                {"value": "week", "label": "Week"},
                {"value": "month", "label": "Month"},
                {"value": "year", "label": "Year"}
            ]
        },
        {
            "type": "number",
            "paramName": "interval_multiplier",
            "label": "Interval Multiplier",
            "value": "1",
            "description": "Multiplier for the interval (e.g., 5 for every 5 minutes)"
        },
        {
            "type": "date",
            "paramName": "start_date",
            "label": "Start Date",
            "value": "2024-09-08",
            "description": "Start date for historical data"
        },
        {
            "type": "date",
            "paramName": "end_date",
            "label": "End Date",
            "value": "2025-09-08",
            "description": "End date for historical data"
        }
    ]
})
@equity_hk_router.get("/prices")
def get_prices_hk(
    ticker: str,
    interval: str,
    interval_multiplier: int,
    start_date: str,
    end_date: str
):
    """Get historical stock prices"""
    from fin_data.profile import get_historical_prices
    stock_prices = get_historical_prices(ticker, interval, interval_multiplier, start_date, end_date)
    return stock_prices.reset_index().to_dict(orient="records")

@register_widget({
    "name": "港股新闻",
    "description": "Get recent news articles for stocks, including headlines, publish dates, and article summaries.",
    "category": "Equity",
    "subcategory": "News",
    "type": "table",
    "widgetId": "hk/news",
    "endpoint": "hk/news",
    "gridData": {
        "w": 40,
        "h": 8
    },
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {"field": "date", "headerName": "Date", "width": 180, "cellDataType": "text", "pinned": "left"},
                {"field": "title", "headerName": "Title", "width": 300, "cellDataType": "text"},
                {"field": "source", "headerName": "Source", "width": 150, "cellDataType": "text"},
                {"field": "author", "headerName": "Author", "width": 150, "cellDataType": "text"},
                {"field": "sentiment", "headerName": "Sentiment", "width": 120, "cellDataType": "text"},
                {"field": "url", "headerName": "URL", "width": 200, "cellDataType": "text"}
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Stock ticker to get news",
            "multiSelect": False,
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "number",
            "paramName": "limit",
            "label": "Number of Articles",
            "value": "10",
            "description": "Maximum number of news articles to display"
        }
    ]
})
@equity_hk_router.get("/news")
async def get_stock_news(ticker: str = Query(..., description="Stock ticker"), 
                         limit: int = 10, token: str = Depends(get_current_user)):
    """Get news articles for a stock"""
    from fin_data.profile import get_news
    return get_news(ticker, limit).to_dict(orient="records")

@register_widget({
    "name": "港股财务指标",
    "description": "获取港股的财务指标",
    "category": "Equity",
    "subcategory": "Financials",
    "type": "table",
    "widgetId": "financial_data",
    "endpoint": "hk/financial_data",
    "gridData": {
        "w": 80,
        "h": 12
    },
    "data": {
        "table": {
            "showAll": True
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Stock ticker",
            "optionsEndpoint": "hk/tickers"
        }
    ]
})
@equity_hk_router.get("/financial_data")
def get_financial_data(
    ticker: str
):
    """Get historical stock prices"""
    from openbb_akshare.utils.ak_compare_company_facts import fetch_compare_company
    from mysharelib.tools import normalize_symbol

    _, symbol_f, _ = normalize_symbol(ticker)

    df_comparison = fetch_compare_company(symbol_f)
    return df_comparison.to_dict(orient="records")

@register_widget({
    "name": "港股利润表",
    "description": "Financial statements that provide information about a company's revenues, expenses, and profits over a specific period.",
    "category": "Equity",
    "subcategory": "Financials",
    "widgetType": "individual",
    "widgetId": "hk/income",
    "endpoint": "hk/income",
    "gridData": {
        "w": 80,
        "h": 12
    },
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "period_ending",
                    "headerName": "报告日期",
                    "cellDataType": "text",
                    "formatterFn": "none",
                    "pinned": "left"
                },
                {
                    "field": "fiscal_period",
                    "headerName": "报告类型",
                    "headerTooltip": "Total Value Locked",
                    "cellDataType": "text",
                    "formatterFn": "none"
                }
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Ticker to get 港股利润表",
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "text",
            "value": "annual",
            "paramName": "period",
            "label": "Period",
            "description": "Period to get statements from",
            "options": [
                {"value": "annual", "label": "Annual"},
                {"value": "quarter", "label": "Quarterly"},
                {"value": "ttm", "label": "TTM"}
            ]
        },
        {
            "type": "number",
            "paramName": "limit",
            "label": "Number of Statements",
            "value": "10",
            "description": "Number of statements to display"
        }
    ]
})
@equity_hk_router.get("/income")
def get_hk_income(ticker: str, period: str, limit: int, token: str = Depends(get_current_user)):
    """Get 利润表"""
    from fin_data.financials import get_income
    income_data = get_income(ticker, period, limit)
    income_data = income_data.fillna(0)
    #logger.info(f"Income data for {ticker}, period: {period}, limit: {limit}: {income_data}")
    return income_data.to_dict(orient="records")

@register_widget({
    "name": "港股资产负债表",
    "description": "A financial statement that summarizes a company's assets, liabilities and shareholders' equity at a specific point in time.",
    "category": "Equity",
    "subcategory": "Financials",
    "type": "table",
    "widgetId": "hk/balance",
    "endpoint": "hk/balance",
    "gridData": {
        "w": 80,
        "h": 12
    },
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "period_ending",
                    "headerName": "报告日期",
                    "cellDataType": "text",
                    "formatterFn": "none",
                    "pinned": "left"
                },
                {
                    "field": "fiscal_period",
                    "headerName": "报告类型",
                    "headerTooltip": "Total Value Locked",
                    "cellDataType": "text",
                    "formatterFn": "none"
                }
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Ticker to get 资产负债表",
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "text",
            "value": "annual",
            "paramName": "period",
            "label": "Period",
            "description": "Period to get statements from",
            "options": [
                {"value": "annual", "label": "Annual"},
                {"value": "quarter", "label": "Quarterly"},
                {"value": "ttm", "label": "TTM"}
            ]
        },
        {
            "type": "number",
            "paramName": "limit",
            "label": "Number of Statements",
            "value": "10",
            "description": "Number of statements to display"
        }
    ]
})
@equity_hk_router.get("/balance")
def get_hk_balance(ticker: str, period: str, limit: int, token: str = Depends(get_current_user)):
    """Get 资产负债表"""
    from fin_data.financials import get_balance
    balance_data = get_balance(ticker, period, limit)
    balance_data = balance_data.fillna(0)
    return balance_data.to_dict(orient="records")

@register_widget({
    "name": "港股现金流量表",
    "description": "Financial statements that provide information about a company's cash inflows and outflows over a specific period.",
    "category": "Equity",
    "subcategory": "Financials",
    "widgetType": "individual",
    "widgetId": "hk/cash_flow",
    "endpoint": "hk/cash_flow",
    "gridData": {
        "w": 80,
        "h": 12
    },
    "data": {
        "table": {
            "showAll": True,
            "columnsDefs": [
                {
                    "field": "period_ending",
                    "headerName": "报告日期",
                    "cellDataType": "text",
                    "formatterFn": "none",
                    "pinned": "left"
                },
                {
                    "field": "fiscal_period",
                    "headerName": "报告类型",
                    "headerTooltip": "Total Value Locked",
                    "cellDataType": "text",
                    "formatterFn": "none"
                }
            ]
        }
    },
    "params": [
        {
            "type": "endpoint",
            "paramName": "ticker",
            "label": "Symbol",
            "value": "00300",
            "description": "Ticker to get 现金流量表",
            "optionsEndpoint": "hk/tickers"
        },
        {
            "type": "text",
            "value": "annual",
            "paramName": "period",
            "label": "Period",
            "description": "Period to get statements from",
            "options": [
                {"value": "annual", "label": "Annual"},
                {"value": "quarter", "label": "Quarterly"},
                {"value": "ttm", "label": "TTM"}
            ]
        },
        {
            "type": "number",
            "paramName": "limit",
            "label": "Number of Statements",
            "value": "10",
            "description": "Number of statements to display"
        }
    ]
})
@equity_hk_router.get("/cash_flow")
def get_hk_cash_flow(ticker: str, period: str, limit: int, token: str = Depends(get_current_user)):
    """Get 现金流量表"""
    from fin_data.financials import get_cash_flow
    cash_data = get_cash_flow(ticker, period, limit)
    cash_data = cash_data.fillna(0)
    return cash_data.to_dict(orient="records")
