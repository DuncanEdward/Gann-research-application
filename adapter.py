from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from types import ModuleType
from contextlib import redirect_stdout
import io
import re
import pandas as pd

# Swiss Ephemeris and stdout redirection have process-wide state. Serialise engine
# operations while retaining separate module globals and files for each session.
ENGINE_LOCK = RLock()
CORE = Path(__file__).with_name('notebook_core.py').read_text(encoding='utf-8')


def parse_tickers(text):
    result = []
    for token in re.split(r'[\s,;]+', text.strip()):
        if not token:
            continue
        token = token.upper().replace('.', '-')
        if not re.fullmatch(r'[A-Z0-9^][A-Z0-9^=\-]{0,19}', token):
            raise ValueError(f'Invalid ticker: {token}')
        if token not in result:
            result.append(token)
    return result


def read_csv(data):
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=encoding, dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    raise ValueError('Could not read CSV encoding.')


def tickers_from_csv(data):
    df = read_csv(data)
    column = next((c for c in df.columns if c.strip().lower() in ('ticker', 'symbol')), None)
    if column is None:
        raise ValueError('The watchlist CSV needs a Ticker or Symbol column (Finviz exports are supported).')
    result = parse_tickers(' '.join(df[column].tolist()))
    if not result:
        raise ValueError('The watchlist contains no tickers.')
    return result


class ResearchEngine:
    def __init__(self):
        self._work = TemporaryDirectory(prefix='bucholtz-session-')
        self.core = ModuleType('bucholtz_session_engine')
        self.core.REPORT_DIR = self._work.name
        self.core.display = lambda *args, **kwargs: None
        with ENGINE_LOCK, redirect_stdout(io.StringIO()):
            exec(compile(CORE, 'notebook_core.py', 'exec'), self.core.__dict__)
        self.core.LAST_SCAN_RESULTS = {'date': None, 'mode': None, 'stocks': [], 'commodities': []}
        self.log = ''
        self.exports = {}

    def call(self, name, *args, **kwargs):
        output = io.StringIO()
        try:
            with ENGINE_LOCK, redirect_stdout(output):
                return getattr(self.core, name)(*args, **kwargs)
        finally:
            self.log += output.getvalue()

    def load_database(self, data=None):
        if data is not None:
            df = read_csv(data)
            df.columns = [c.strip() for c in df.columns]
            if not {'Ticker', 'Date'}.issubset(df.columns) or df.empty:
                raise ValueError('First-trade CSV needs Ticker and Date columns and at least one record.')
            dates = pd.to_datetime(df['Date'], errors='coerce')
            if dates.isna().any():
                raise ValueError('First-trade CSV contains invalid dates. Correct them before uploading.')
            if df['Ticker'].str.strip().eq('').any():
                raise ValueError('First-trade CSV contains empty tickers.')
            path = Path(self._work.name) / 'first_trades.csv'
            df.to_csv(path, index=False)
            result = self.call('load_first_trade_database', str(path))
        else:
            result = self.call('load_first_trade_database')
        if result is None or result.empty:
            raise ValueError('No usable first-trade database records.')
        return len(result)

    def scan(self, date, mode='before_market', market='stocks', universe='liquid',
             tickers=None, long_only=True, top_n=8, max_symbols=60):
        self.exports = {}
        effective, note = self.call('_validated_market_mode', date, mode)
        state = {'date': date, 'requested_mode': mode, 'mode': effective,
                 'mode_note': note, 'stocks': [], 'commodities': []}
        # Commit only a fully completed scan. Failures leave no partial report.
        self.core.LAST_SCAN_RESULTS = state
        original_default = self.core.DEFAULT_STOCKS
        try:
            if market in ('stocks', 'both'):
                if tickers is not None:
                    if not tickers:
                        raise ValueError('Enter or upload at least one ticker.')
                    if len(tickers) > max_symbols:
                        raise ValueError(f'{len(tickers)} tickers exceed the {max_symbols}-symbol limit. Increase the limit or shorten the list.')
                    self.core.DEFAULT_STOCKS = list(tickers)
                    universe = 'liquid'
                state['stocks'] = self.call('scan_stocks', date, universe, long_only, top_n, max_symbols, effective, True)
                if not state['stocks']:
                    raise RuntimeError('No stock results. Yahoo may be unavailable, or no symbols passed the notebook technical prefilter. Try a smaller list or another date.')
            if market in ('commodities', 'both'):
                state['commodities'] = self.call('scan_commodities', date, long_only, top_n, effective, True)
                if not state['commodities']:
                    raise RuntimeError('No commodity results. Check market-data availability.')
            return state
        except Exception:
            self.core.LAST_SCAN_RESULTS = {'date': None, 'mode': None, 'stocks': [], 'commodities': []}
            raise
        finally:
            self.core.DEFAULT_STOCKS = original_default

    def timing(self):
        self.exports = {}
        return self.call('compute_timing_continuum_for_selected_results')

    def reports(self):
        # Preserve the final V10.2.2 wrapper: continuum, then original renderer.
        exports = {}
        for label, function, mime in [('PDF', 'make_pdf_report', 'application/pdf'),
                                       ('CSV', 'make_csv_report', 'text/csv'),
                                       ('HTML', 'make_html_report', 'text/html')]:
            path = Path(self.call(function))
            exports[label] = (path.name, path.read_bytes(), mime)
        self.exports = exports
        return exports

    def close(self):
        self._work.cleanup()
