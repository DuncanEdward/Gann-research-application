import hmac
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from engine.adapter import ResearchEngine, parse_tickers, tickers_from_csv

st.set_page_config(page_title='Bucholtz · Meridian · McWhirter', page_icon='◉', layout='wide')
password = os.environ.get('APP_PASSWORD', '')
if password and not st.session_state.get('authenticated'):
    st.title('Market Research Engine')
    entered = st.text_input('Password', type='password')
    if st.button('Sign in'):
        if hmac.compare_digest(entered.encode(), password.encode()):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error('Incorrect password.')
    st.stop()

st.title('Bucholtz · Meridian · McWhirter')
st.caption('Financial market research • V10.2.3 engine • First-trade analysis and price confirmation')
st.info('Research only. Scores are model rankings, not probabilities or proven returns. Price confirmation and invalidation remain essential. No orders are placed.')

with st.sidebar:
    st.header('Scan controls')
    scan_date = st.date_input('Trading date', datetime.now(ZoneInfo('America/New_York')).date())
    mode_labels = {'Before market': 'before_market', 'During market': 'during_market', 'After market': 'after_market'}
    mode = st.selectbox('Requested market mode', list(mode_labels))
    market = st.selectbox('Markets', ['Stocks', 'Commodities', 'Both'])
    source = st.radio('Stock selection', ['Manual tickers', 'Finviz / watchlist CSV', 'Liquid US universe', 'S&P 500'])
    manual = st.text_area('Tickers, separated by commas or spaces', 'NVDA, AMD, PLTR', disabled=source != 'Manual tickers')
    watchlist = st.file_uploader('Upload Finviz / watchlist CSV', type=['csv'], disabled=source != 'Finviz / watchlist CSV')
    first_trade = st.file_uploader('Replace first-trade database (optional)', type=['csv'], help='Ticker and Date are required. Optional: name, ipo_time, Place, market_tz, source_note, source_quality. Replaces the database for this scan, rather than merging.')
    long_only = st.checkbox('Long ideas only', value=True)
    st.caption('Inherited notebook filter: short setups may remain visible as NO TRADE research rows.')
    top_n = st.slider('Results per market', 3, 15, 8)
    limit = st.slider('Maximum stock symbols', 10, 500, 60, 10)
    calculate_timing = st.checkbox('Calculate timing for final results', value=True)
    run = st.button('Run analysis', type='primary', use_container_width=True)
    st.caption('S&P 500 scans use the first N symbols in the source list. Raise the limit to scan more. Timing labels follow New York time.')

if run:
    # A new engine gives every scan a clean database/cache and private output folder.
    previous = st.session_state.pop('engine', None)
    if previous:
        previous.close()
    st.session_state.pop('results', None)
    try:
        tickers = None
        if market != 'Commodities':
            if source == 'Manual tickers':
                tickers = parse_tickers(manual)
            elif source == 'Finviz / watchlist CSV':
                if watchlist is None:
                    raise ValueError('Upload your Finviz or watchlist CSV first.')
                tickers = tickers_from_csv(watchlist.getvalue())
        with st.spinner('Running the original scoring engine…'):
            engine = ResearchEngine()
            st.session_state.engine = engine
            rows = engine.load_database(first_trade.getvalue() if first_trade else None)
            result = engine.scan(scan_date.isoformat(), mode_labels[mode], market.lower(),
                                 'sp500' if source == 'S&P 500' else 'liquid', tickers,
                                 long_only, top_n, limit)
            if calculate_timing:
                engine.timing()
            st.session_state.results = result
            st.session_state.database_rows = rows
    except Exception as exc:
        st.error(f'Analysis did not complete: {exc}')

engine = st.session_state.get('engine')
results = st.session_state.get('results')
if results and engine:
    st.subheader(f"Results · {results['date']}")
    st.caption(results['mode_note'])
    st.caption(f"First-trade database: {st.session_state.database_rows:,} rows. Data quality labels describe the source records; they do not independently certify historical accuracy.")
    ideas = results['commodities'] + results['stocks']
    table = engine.call('summary_dataframe', ideas)
    table.insert(2, 'Status', [i['status'] for i in ideas])
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption('Market R:R = potential reward to the market-derived target ÷ distance to invalidation. The 1.67R target is a separate risk-based reference.')
    for rank, idea in enumerate(ideas, 1):
        with st.expander(f"{rank}. {idea['ticker']} · {idea['status']} · {idea['bias']} · selection {idea.get('v9_selection_score', 0)}"):
            st.write(f"Price data through: {idea['data_asof']} · First trade: {idea.get('first_trade') or 'Unavailable'}")
            st.write(idea.get('first_trade_note', ''))
            st.json(engine.call('_trade_plan_metrics', idea), expanded=True)
            for label, key in [('Bucholtz evidence', 'reason_sections'), ('Meridian', 'meridian'), ('McWhirter chapters', 'mcwhirter'), ('Decision and execution', 'decision_v84'), ('Overnight / premarket / session timing', 'v102_timing_plan')]:
                st.markdown(f'**{label}**')
                st.json(idea.get(key, idea.get('decision_v83', {}) if key == 'decision_v84' else {}), expanded=False)
            with st.expander('All evidence and timing events'):
                st.json(idea, expanded=False)
    c1, c2 = st.columns(2)
    if c1.button('Calculate / refresh selected timing'):
        try:
            with st.spinner('Calculating timing…'):
                engine.call('compute_timing_continuum_for_selected_results', force=True)
                engine.exports = {}
            st.rerun()
        except Exception as exc:
            st.error(f'Timing failed: {exc}')
    if c2.button('Prepare PDF, CSV and HTML reports'):
        try:
            with st.spinner('Preparing reports…'):
                engine.reports()
            st.rerun()
        except Exception as exc:
            st.error(f'Report generation failed: {exc}')
    if engine.exports:
        cols = st.columns(3)
        for col, (label, (name, data, mime)) in zip(cols, engine.exports.items()):
            col.download_button(f'Download {label}', data, file_name=name, mime=mime)
        st.caption('PDF and CSV use the final notebook exporters. HTML retains the notebook’s legacy V8.4 view; use PDF for the complete McWhirter and V10.2 timing report.')
    with st.expander('Database and source audit'):
        if st.button('Validate selected first-trade records'):
            validation = engine.call('validate_selected_first_trade_records')
            st.dataframe(validation, hide_index=True)
        if st.button('Prepare bundled database and 2026–2030 calendar'):
            st.session_state.reference_downloads = {
                'first_trades_IPOs_clean_Bucholtz_markets.csv': engine.call('_v10_embedded_first_trade_df').to_csv(index=False).encode(),
                'Bucholtz_calendar_2026_2030.csv': engine.call('_v10_embedded_calendar_df').to_csv(index=False).encode(),
            }
        for name, data in st.session_state.get('reference_downloads', {}).items():
            st.download_button(name, data, file_name=name, mime='text/csv')
        st.json(engine.core.RULEBOOK, expanded=False)
    with st.expander('Run log'):
        st.code(engine.log or 'No additional messages.')
else:
    st.write('Choose your tickers or upload a Finviz CSV, then run analysis. The bundled first-trade database is used unless you upload a replacement.')
