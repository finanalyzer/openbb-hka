import sys
import types
import importlib
import asyncio
from types import SimpleNamespace
import pytest
import pandas as pd
from fastapi import HTTPException

# Provide fake dependencies before importing the module under test
if "openbb" not in sys.modules:
    openbb_mod = types.ModuleType("openbb")
    # minimal obb structure expected by the module
    obb = SimpleNamespace()
    obb.equity = SimpleNamespace()
    obb.equity.price = SimpleNamespace()
    # set placeholders; tests will monkeypatch these
    obb.equity.price.historical = lambda *a, **k: SimpleNamespace(to_dataframe=lambda: pd.DataFrame())
    obb.equity.search = lambda *a, **k: SimpleNamespace(to_dataframe=lambda: pd.DataFrame())
    openbb_mod.obb = obb
    sys.modules["openbb"] = openbb_mod

# fake core.registry.register_widget used in the module
if "core.registry" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_registry = types.ModuleType("core.registry")
    def register_widget(*a, **k):
        return None
    core_registry.register_widget = register_widget
    sys.modules["core"] = core_pkg
    sys.modules["core.registry"] = core_registry

# import the module under test
tv = importlib.import_module("routes.tradingview")


@pytest.mark.asyncio
async def test_provider_returns_none_results_in_no_data(monkeypatch):
    # historical returns None -> should result in {"s": "no_data"}
    def fake_historical(*a, **k):
        return SimpleNamespace(to_dataframe=lambda: None)
    monkeypatch.setattr(tv.obb.equity.price, "historical", fake_historical)
    res = await tv.get_history(symbol="AAA", resolution="D", from_time=1577836800, to_time=1577923200)
    assert res == {"s": "no_data"}


@pytest.mark.asyncio
async def test_daily_resolution_returns_ok_and_ohlcv(monkeypatch):
    # create daily data for 3 days
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    df = pd.DataFrame({
        "open": [1, 2, 3],
        "high": [1.5, 2.5, 3.5],
        "low": [0.8, 1.8, 2.8],
        "close": [1.2, 2.2, 3.2],
        "volume": [100, 200, 300],
    }, index=idx)

    monkeypatch.setattr(tv.obb.equity.price, "historical", lambda *a, **k: SimpleNamespace(to_dataframe=lambda: df))
    from_ts = int(pd.Timestamp("2020-01-01").timestamp())
    to_ts = int(pd.Timestamp("2020-01-03 23:59:59").timestamp())
    res = await tv.get_history(symbol="AAA", resolution="D", from_time=from_ts, to_time=to_ts)

    assert res["s"] == "ok"
    assert len(res["t"]) == 3
    assert len(res["o"]) == 3
    assert len(res["h"]) == 3
    assert len(res["l"]) == 3
    assert len(res["c"]) == 3
    assert len(res["v"]) == 3
    # sample values
    assert res["o"][0] == float(df["open"].iloc[0])
    assert res["c"][-1] == float(df["close"].iloc[-1])


@pytest.mark.asyncio
async def test_numeric_minute_resolution_with_daily_data_returns_no_data(monkeypatch):
    # data spaced by 1 day -> numeric minute resolution should detect no intraday and return no_data
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    df = pd.DataFrame({"open": [1,2,3,4,5], "high":[1,2,3,4,5], "low":[1,2,3,4,5], "close":[1,2,3,4,5], "volume":[1,1,1,1,1]}, index=idx)
    monkeypatch.setattr(tv.obb.equity.price, "historical", lambda *a, **k: SimpleNamespace(to_dataframe=lambda: df))
    from_ts = int(pd.Timestamp("2020-01-01").timestamp())
    to_ts = int(pd.Timestamp("2020-01-05").timestamp())
    res = await tv.get_history(symbol="AAA", resolution="5", from_time=from_ts, to_time=to_ts)
    assert res == {"s": "no_data"}


@pytest.mark.asyncio
async def test_numeric_minute_resolution_intraday_resamples_and_returns_ok(monkeypatch):
    # intraday minute data (1-minute intervals) should be resampled for a 5-minute resolution
    idx = pd.date_range("2020-01-02 09:30", periods=10, freq="1T")  # 10 minutes
    df = pd.DataFrame({
        "open": range(10),
        "high": [x + 0.5 for x in range(10)],
        "low": [x - 0.5 for x in range(10)],
        "close": [x + 0.1 for x in range(10)],
        "volume": [10]*10
    }, index=idx)

    monkeypatch.setattr(tv.obb.equity.price, "historical", lambda *a, **k: SimpleNamespace(to_dataframe=lambda: df))
    from_ts = int(pd.Timestamp("2020-01-02 09:30").timestamp())
    to_ts = int(pd.Timestamp("2020-01-02 09:39").timestamp())
    res = await tv.get_history(symbol="AAA", resolution="5", from_time=from_ts, to_time=to_ts)

    assert res["s"] == "ok"
    # 10 minutes with 5T resampling -> expect 2 buckets
    assert len(res["t"]) == 2
    assert len(res["o"]) == 2
    assert all(isinstance(x, (float, type(None))) for x in res["o"])


@pytest.mark.asyncio
async def test_invalid_timestamps_raise_http_exception():
    # invalid from_time should raise HTTPException with status_code 400
    with pytest.raises(HTTPException) as exc:
        await tv.get_history(symbol="AAA", resolution="D", from_time="not_a_timestamp", to_time=1577923200)
    assert exc.value.status_code == 400