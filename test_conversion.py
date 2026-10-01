import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from engine.adapter import ResearchEngine, parse_tickers, tickers_from_csv

ROOT = Path(__file__).resolve().parents[1]


def test_preserved_function_bodies():
    notebook = json.loads(next((ROOT / 'source').glob('*.ipynb')).read_text())
    extracted = [n for n in ast.parse((ROOT/'engine/notebook_core.py').read_text()).body if isinstance(n, ast.FunctionDef)]
    source_functions = []
    for index in [10,13,19,21,23,26,27,29,31,38,41,43,44,47,49,53,55,59,60,63]:
        text = ''.join(notebook['cells'][index]['source'])
        text = text.replace("Path('/content' if Path('/content').exists() else '/mnt/data')", 'Path(REPORT_DIR)').replace('Path("/content" if Path("/content").exists() else "/mnt/data")', 'Path(REPORT_DIR)')
        for n in ast.parse(text).body:
            if not isinstance(n, ast.FunctionDef): continue
            if index == 23 and n.name not in ('show_detail', '_validated_market_mode'): continue
            if index == 27 and n.name in ('_download', 'on_pdf', 'on_csv', 'on_html'): continue
            source_functions.append(n)
    assert len(extracted) == len(source_functions)
    for a, b in zip(extracted, source_functions):
        assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False), a.name


def test_watchlist_inputs():
    assert parse_tickers('nvda, AMD\nNVDA; brk.b') == ['NVDA', 'AMD', 'BRK-B']
    assert tickers_from_csv(b'No.,Ticker,Price\n1,NVDA,100\n2,AMD,80\n') == ['NVDA', 'AMD']
    with pytest.raises(ValueError): tickers_from_csv(b'Price\n100\n')
    with pytest.raises(ValueError): parse_tickers('NVDA <script>')


def test_session_isolation_and_upload_validation():
    a, b = ResearchEngine(), ResearchEngine()
    try:
        assert a.core.V102_SKY_CACHE is not b.core.V102_SKY_CACHE
        assert a.core.REPORT_DIR != b.core.REPORT_DIR
        assert a.core.FIRST_TRADE_DB is None
        assert a.core.V10_BUCHOLTZ_CALENDAR is None
        assert a.load_database(b'Ticker,Date,ipo_time\nTEST,2020-01-02,09:30\n') == 1
        assert a.call('lookup_first_trade_record', 'TEST')['quality'] == 'VERIFIED_TIME'
        assert b.core.FIRST_TRADE_DB is None
        with pytest.raises(ValueError): a.load_database(b'Ticker,Date\nTEST,invalid\n')
    finally:
        a.close(); b.close()


def fixture_history(*args, **kwargs):
    index = pd.bdate_range('2023-01-02', '2026-09-30')
    x = np.arange(len(index))
    close = 40 + x * .08 + np.sin(x / 8) * 2
    return pd.DataFrame({'Open':close-.3, 'High':close+1, 'Low':close-1, 'Close':close,
                         'Volume':np.full(len(x), 3000000)}, index=index)


def test_end_to_end_offline_reports():
    engine = ResearchEngine()
    try:
        engine.load_database(b'Ticker,Date,name,ipo_time,market_tz\nTEST,2020-01-02,Test Company,09:30,America/New_York\n')
        engine.core.fetch_history = fixture_history
        state = engine.scan('2026-09-30', tickers=['TEST'], top_n=3)
        assert state['mode'] == 'after_market'
        assert len(state['stocks']) == 1
        idea = state['stocks'][0]
        assert 'meridian' in idea and 'mcwhirter' in idea
        assert 'v102_timing_continuum' not in idea
        engine.timing()
        assert 'v102_timing_continuum' in idea
        assert engine.call('summary_dataframe', [idea]).iloc[0]['Ticker'] == 'TEST'
        exports = engine.reports()
        assert exports['PDF'][1].startswith(b'%PDF')
        assert b'TEST' in exports['CSV'][1]
        assert b'<html' in exports['HTML'][1].lower()
        assert all(Path(engine.core.REPORT_DIR, item[0]).exists() for item in exports.values())
        # A failed next scan must clear reports and partial results.
        engine.core.fetch_history = lambda *a, **k: pd.DataFrame()
        with pytest.raises(RuntimeError): engine.scan('2026-09-30', tickers=['TEST'])
        assert engine.exports == {}
        assert engine.core.LAST_SCAN_RESULTS['stocks'] == []
    finally:
        engine.close()
